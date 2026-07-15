import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Set

from src.config import settings
from src.reconciliation_gate import (
    reconciliation_gate,
    stop_signal_flagged,
    clear_reconciliation_stop,
)
from src.idle_sentinel import IdleSentinel
from src.progress_tracker import update as progress_update, increment as progress_inc

logger = logging.getLogger("chickensoup.wiki.watcher")

# Slugs created by the watcher's own entity extraction, used to prevent
# recursive processing loops when the watcher creates sub-pages that
# then trigger additional filesystem events.
_WATCHER_CREATED: Set[str] = set()


def _wiki_dirs() -> Set[str]:
    wiki_root = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_root):
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wiki_root = os.path.join(base, wiki_root)
    return {
        os.path.join(wiki_root, sub)
        for sub in ("entities", "concepts", "projects")
    }


def _run_llm_entity_extraction(slug: str, title: str, subdir: str, body: str, tags: list = None) -> None:
    """Run LLM-powered entity extraction on page body to discover sub-entities.

    Passes the page body through IngestAgent.analyze_content so the LLM can
    identify entities, concepts, or projects mentioned in the text that don't
    yet have their own wiki page. New sub-pages are created, cross-referenced,
    and ingested to Neo4j through the full pipeline.

    Skips entity extraction for:
      - Pages that were themselves created by this function (recursion guard)
      - Engineering-only pages (no content tags)
    """
    if slug in _WATCHER_CREATED:
        logger.debug(f"Skipping LLM entity extraction for watcher-created page '{slug}'")
        return

    # P3: Skip LLM extraction for engineering-only pages
    from src.wiki.cleanup import ENGINEERING_TAGS, CONTENT_TAGS
    tag_set = set(str(t).lower() for t in (tags or []))
    if bool(tag_set & ENGINEERING_TAGS) and not bool(tag_set & CONTENT_TAGS):
        logger.debug(f"Skipping LLM extraction for engineering-only page '{slug}'")
        return

    from src.agents.ingest_agent import IngestAgent
    from src.wiki.writer import write_page, cross_reference_new_page, invalidate_index_cache
    from src.knowledge_graph.connection import neo4j_conn
    from src.knowledge_graph.ingest import ingest_wiki_page
    from src.staleness_queue import record_pulse_completed

    try:
        agent = IngestAgent()
    except Exception as e:
        logger.warning(f"LLM extraction: could not create IngestAgent for '{slug}': {e}")
        return

    try:
        analysis = agent.analyze_content(body, filename=f"{slug}.md")
    except Exception as e:
        logger.warning(f"LLM extraction: analyze_content failed for '{slug}': {e}")
        return

    if not analysis.suggested_pages:
        return

    driver = neo4j_conn.get_driver()

    created_any = False
    for page in analysis.suggested_pages:
        if page.confidence < settings.WIKI_MIN_CONFIDENCE:
            continue
        if not settings.WIKI_AUTO_CREATE:
            break

        page_type = page.page_type
        if page_type not in ("entities", "concepts", "projects"):
            page_type = agent.classify_page_type(page.title, page.summary, page.tags)

        sub_slug, is_new = write_page(
            title=page.title,
            body=page.body,
            tags=page.tags,
            sources=page.sources,
            related=page.related,
            page_type=page_type,
        )

        _WATCHER_CREATED.add(sub_slug)

        try:
            cross_reference_new_page(sub_slug, page.title, page_type)
        except Exception as xref_err:
            logger.warning(f"LLM extraction: cross-ref failed for '{page.title}': {xref_err}")

        if driver:
            full = (
                f"---\ntitle: {page.title}\ntags: {page.tags}\n"
                f"sources: {page.sources}\nrelated: {page.related}\n---\n\n{page.body}"
            )
            try:
                ingest_wiki_page(driver, title=page.title, content=full)
            except Exception as neo4j_err:
                logger.warning(f"LLM extraction: Neo4j ingest failed for '{page.title}': {neo4j_err}")

        try:
            record_pulse_completed(sub_slug, divergence_risk=0.0, state_label="unverified")
        except Exception as queue_err:
            logger.warning(f"LLM extraction: queue seed failed for '{sub_slug}': {queue_err}")

        created_any = True

    if created_any:
        invalidate_index_cache()
        logger.info(f"LLM extraction: created {len(analysis.suggested_pages)} sub-entities from '{slug}'")


def _ingest_page(slug: str, subdir: str) -> None:
    """Run full ingestion pipeline for a single wiki page.

    Includes LLM-powered entity extraction (discovers sub-entities from body),
    cross-referencing, Neo4j ingest with LLM edge classification, index/log
    updates, and staleness queue seeding.

    Neo4j MERGE operations make this safe to call for already-ingested pages.
    Idempotent by design.
    """
    from src.wiki.writer import (
        read_page, cross_reference_new_page, append_to_index, append_to_log,
        invalidate_index_cache,
    )
    from src.knowledge_graph.ingest import ingest_wiki_page
    from src.staleness_queue import record_pulse_completed
    from src.knowledge_graph.connection import neo4j_conn

    page_data = read_page(slug, page_type=subdir)
    if not page_data or "frontmatter" not in page_data:
        logger.warning(f"Ingest: cannot read page '{slug}' in '{subdir}'")
        return

    title = page_data["frontmatter"].get("title", slug)
    tags = page_data["frontmatter"].get("tags", [])
    sources = page_data["frontmatter"].get("sources", [])
    related = page_data["frontmatter"].get("related", [])
    body = page_data.get("body", "")
    full_content = f"---\ntitle: {title}\ntags: {tags}\nsources: {sources}\nrelated: {related}\n---\n\n{body}"

    _run_llm_entity_extraction(slug, title, subdir, body, tags=tags)

    try:
        cross_reference_new_page(slug, title, subdir)
    except Exception as xref_err:
        logger.warning(f"Ingest: cross-reference failed for '{slug}': {xref_err}")

    driver = neo4j_conn.get_driver()
    if driver:
        try:
            ingest_wiki_page(driver, title=title, content=full_content, default_tags=tags, default_sources=sources)
        except Exception as neo4j_err:
            logger.warning(f"Ingest: Neo4j ingest failed for '{slug}': {neo4j_err}")

    try:
        append_to_index([(slug, title, subdir)])
    except Exception as idx_err:
        logger.warning(f"Ingest: index update failed for '{slug}': {idx_err}")

    try:
        append_to_log(f"Watcher ingest: {slug} ({subdir})")
    except Exception as log_err:
        logger.warning(f"Ingest: log update failed for '{slug}': {log_err}")

    invalidate_index_cache()
    record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
    logger.info(f"Ingest: processed page '{slug}' ({subdir})")


async def _on_file_event(change_type: str, path_str: str) -> None:
    """Handle a single filesystem event from the watcher.

    Dispatches the ingestion work to a thread executor to avoid blocking
    the event loop during LLM calls and Neo4j operations.
    """
    if not path_str.endswith(".md"):
        return
    slug = os.path.splitext(os.path.basename(path_str))[0]
    subdir = os.path.basename(os.path.dirname(path_str))
    logger.info(f"Watcher: {change_type} page '{slug}' ({subdir})")

    if reconciliation_gate.is_busy():
        logger.debug(f"Watcher: skipping '{slug}' — reconciliation in progress")
        return

    # Phase 1.7: Handle deleted pages — remove from Neo4j and staleness queue
    if change_type == "deleted":
        node_name = slug.replace("-", " ")
        try:
            from src.knowledge_graph.connection import neo4j_conn
            driver = neo4j_conn.get_driver()
            if driver:
                with driver.session() as session:
                    session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n", name=node_name)
                logger.info(f"Watcher: deleted Neo4j node for '{slug}'")
            from src.cache import cache_store
            cache_store.invalidate_entity(node_name)
            if cache_store.redis_client:
                cache_store.redis_client.zrem("staleness:queue", slug)
            try:
                from src.main import _sse_broadcast
                import asyncio
                asyncio.ensure_future(_sse_broadcast("entity_deleted", node_name, source="watcher"))
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Watcher: failed to clean up deleted page '{slug}': {e}")
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _ingest_page, slug, subdir)


def reconcile_existing_pages():
    """Reconciliation: run full ingestion for all existing wiki pages.

    Handles pages that were added or restored while the server was
    down (e.g. git checkout, rsync). Runs in a thread executor to avoid
    blocking the event loop during the O(n) cross-reference scan and LLM calls.

    Phase 4/9: Acquires ReconciliationGate, yields to user activity via
    IdleSentinel, and checks a Redis stop signal between pages.
    """
    if not reconciliation_gate.acquire():
        logger.info("Reconciliation skipped — already in progress")
        return

    clear_reconciliation_stop()
    try:
        watched_dirs = _wiki_dirs()
        existing_dirs = [d for d in watched_dirs if os.path.isdir(d)]
        all_pages = []
        for dir_path in existing_dirs:
            subdir = os.path.basename(dir_path)
            for fname in sorted(os.listdir(dir_path)):
                if fname.endswith(".md"):
                    all_pages.append((os.path.splitext(fname)[0], subdir))

        total = len(all_pages)
        logger.info(f"Reconciliation: scanning {total} existing wiki pages...")

        now = datetime.now(timezone.utc).isoformat()
        progress_update("reconciliation",
            status="running", current=0, total=str(total),
            current_slug="", pages_processed="0", errors="0",
            started_at=now, completed_at="")

        count = 0
        errors = 0
        for idx, (slug, subdir) in enumerate(all_pages):
            if stop_signal_flagged():
                logger.info("Reconciliation preempted by stop signal")
                progress_update("reconciliation", status="stopped")
                return

            while not IdleSentinel.is_idle():
                time.sleep(1)
                if stop_signal_flagged():
                    progress_update("reconciliation", status="stopped")
                    return

            try:
                progress_update("reconciliation", current=str(idx + 1), current_slug=slug)
                _ingest_page(slug, subdir)
                count += 1
                reconciliation_gate.refresh_ttl()
            except Exception as e:
                logger.error(f"Reconciliation: failed to process '{slug}': {e}")
                errors += 1
                progress_update("reconciliation", errors=str(errors))

        progress_update("reconciliation",
            status="complete", current=str(total), total=str(total),
            pages_processed=str(count), errors=str(errors),
            completed_at=datetime.now(timezone.utc).isoformat())
        logger.info(f"Reconciliation complete: {count} pages processed, {errors} errors")
    finally:
        reconciliation_gate.release()


async def wiki_watcher_loop():
    """Async filesystem watcher for wiki page changes.

    Watches wiki/{entities,concepts,projects}/ for new/modified .md files
    and runs the full ingestion pipeline including LLM entity extraction
    and edge classification. All I/O-bound work is offloaded to a thread
    executor to keep the event loop responsive.
    """
    try:
        from watchfiles import awatch
    except ImportError:
        logger.warning("watchfiles not available — wiki watcher disabled")
        return

    watched_dirs = _wiki_dirs()
    existing_dirs = [d for d in watched_dirs if os.path.isdir(d)]
    if not existing_dirs:
        logger.warning("No wiki directories exist — watcher has nothing to watch")
        return

    logger.info(f"Wiki watcher started, watching: {existing_dirs}")
    progress_update("wiki_watcher", status="watching", events_processed="0")

    async for changes in awatch(*existing_dirs):
        for change_type, path_str in changes:
            await _on_file_event(change_type, path_str)
            progress_inc("wiki_watcher", "events_processed")
