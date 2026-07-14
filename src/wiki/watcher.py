import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Set

from src.config import settings

logger = logging.getLogger("chickensoup.wiki.watcher")


def _wiki_dirs() -> Set[str]:
    wiki_root = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_root):
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wiki_root = os.path.join(base, wiki_root)
    return {
        os.path.join(wiki_root, sub)
        for sub in ("entities", "concepts", "projects")
    }


async def wiki_watcher_loop():
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
    async for changes in awatch(*existing_dirs):
        for change_type, path_str in changes:
            if not path_str.endswith(".md"):
                continue
            slug = os.path.splitext(os.path.basename(path_str))[0]
            subdir = os.path.basename(os.path.dirname(path_str))
            try:
                from src.wiki.writer import (
                    read_page, write_page, slugify,
                    cross_reference_new_page, invalidate_index_cache,
                )
                from src.knowledge_graph.ingest import ingest_wiki_page
                from src.staleness_queue import record_pulse_completed
                from src.knowledge_graph.connection import neo4j_conn
                from src.wiki.writer import append_to_index, append_to_log

                page_data = read_page(slug)
                if not page_data or "frontmatter" not in page_data:
                    logger.warning(f"Watcher: cannot read page '{slug}' after change")
                    continue

                title = page_data["frontmatter"].get("title", slug)
                tags = page_data["frontmatter"].get("tags", [])
                sources = page_data["frontmatter"].get("sources", [])
                related = page_data["frontmatter"].get("related", [])
                body = page_data.get("body", "")
                full_content = f"---\ntitle: {title}\ntags: {tags}\nsources: {sources}\nrelated: {related}\n---\n\n{body}"

                if change_type == "added":
                    logger.info(f"Watcher: new page detected '{slug}' ({subdir})")
                    try:
                        cross_reference_new_page(slug, title, subdir)
                    except Exception as xref_err:
                        logger.warning(f"Watcher: cross-reference failed for '{slug}': {xref_err}")
                    try:
                        driver = neo4j_conn.get_driver()
                        if driver:
                            ingest_wiki_page(driver, title=title, content=full_content, default_tags=tags, default_sources=sources)
                    except Exception as neo4j_err:
                        logger.warning(f"Watcher: Neo4j ingest failed for '{slug}': {neo4j_err}")
                    try:
                        append_to_index([(slug, title, subdir)])
                    except Exception as idx_err:
                        logger.warning(f"Watcher: index update failed for '{slug}': {idx_err}")
                    try:
                        append_to_log(f"Watcher auto-ingest: created {slug} ({subdir})")
                    except Exception as log_err:
                        logger.warning(f"Watcher: log update failed for '{slug}': {log_err}")
                    invalidate_index_cache()
                    record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
                    logger.info(f"Watcher: fully ingested new page '{slug}'")
                elif change_type == "modified":
                    logger.info(f"Watcher: modified page detected '{slug}'")
                    try:
                        driver = neo4j_conn.get_driver()
                        if driver:
                            ingest_wiki_page(driver, title=title, content=full_content, default_tags=tags, default_sources=sources)
                    except Exception as neo4j_err:
                        logger.warning(f"Watcher: Neo4j re-ingest failed for '{slug}': {neo4j_err}")
                    invalidate_index_cache()
                    record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
                    logger.info(f"Watcher: re-ingested modified page '{slug}'")
            except Exception as e:
                logger.error(f"Watcher: failed to process change for '{path_str}': {e}", exc_info=True)
