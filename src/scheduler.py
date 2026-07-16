import asyncio
import json
import logging
import os
import re
from datetime import date, datetime, timezone
from typing import List, Optional

from src.config import settings
from src.cache import cache_store
from src.reconciliation_gate import reconciliation_gate

logger = logging.getLogger("chickensoup.scheduler")

_RUNNING = False
_LAST_RUN: Optional[str] = None
_CONVERSATIONS_CHECKED = 0
_CONVERSATIONS_INGESTED = 0
_PAGES_CREATED = 0
_PAGES_UPDATED = 0


def _meta_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:meta"


def _eligible_set_key() -> str:
    return "conversation:eligible"


def get_conversation_meta(conversation_id: str) -> dict:
    raw = cache_store.get(_meta_key(conversation_id))
    return raw if isinstance(raw, dict) else {}


def set_conversation_meta(conversation_id: str, meta: dict):
    cache_store.set(_meta_key(conversation_id), meta, ttl=604800)


def update_conversation_meta(conversation_id: str, updates: dict):
    meta = get_conversation_meta(conversation_id)
    meta.update(updates)
    set_conversation_meta(conversation_id, meta)


def add_eligible_conversation(conversation_id: str):
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.sadd(_eligible_set_key(), conversation_id)
        cache_store.redis_client.expire(_eligible_set_key(), 604800)
    except Exception as e:
        logger.warning(f"Failed to add eligible conversation {conversation_id}: {e}")


def get_eligible_conversations() -> List[str]:
    if not cache_store.redis_client:
        return []
    try:
        return [cid.decode() if isinstance(cid, bytes) else cid
                for cid in cache_store.redis_client.smembers(_eligible_set_key())]
    except Exception as e:
        logger.warning(f"Failed to get eligible conversations: {e}")
        return []


def remove_eligible_conversation(conversation_id: str):
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.srem(_eligible_set_key(), conversation_id)
    except Exception as e:
        logger.warning(f"Failed to remove eligible conversation {conversation_id}: {e}")


def get_all_conversation_ids() -> List[str]:
    if not cache_store.redis_client:
        return []
    try:
        pattern = "conversation:*:meta"
        keys = cache_store.redis_client.keys(pattern)
        ids = []
        for key in keys:
            k = key.decode() if isinstance(key, bytes) else key
            parts = k.split(":")
            if len(parts) >= 2:
                ids.append(parts[1])
        return ids
    except Exception as e:
        logger.warning(f"Failed to scan conversation keys: {e}")
        return []


def is_conversation_idle(conversation_id: str) -> bool:
    meta = get_conversation_meta(conversation_id)
    last_activity_str = meta.get("last_activity")
    if not last_activity_str:
        return True
    try:
        last_activity = datetime.fromisoformat(last_activity_str)
        now = datetime.now(timezone.utc)
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        elapsed = (now - last_activity).total_seconds() / 60
        return elapsed >= settings.CHAT_WIKI_IDLE_TIMEOUT_MINUTES
    except Exception:
        return True


def get_status() -> dict:
    return {
        "enabled": settings.CHAT_WIKI_CONVERSION_ENABLED,
        "last_run": _LAST_RUN,
        "conversations_checked": _CONVERSATIONS_CHECKED,
        "conversations_ingested": _CONVERSATIONS_INGESTED,
        "pages_created": _PAGES_CREATED,
        "pages_updated": _PAGES_UPDATED,
    }


async def periodic_chat_ingest_loop():
    global _RUNNING, _LAST_RUN, _CONVERSATIONS_CHECKED, _CONVERSATIONS_INGESTED
    global _PAGES_CREATED, _PAGES_UPDATED

    _RUNNING = True
    logger.info(f"Chat ingest scheduler started (interval={settings.CHAT_WIKI_CHECK_INTERVAL_SECONDS}s, "
                f"min_messages={settings.CHAT_WIKI_MIN_CONVERSATION_LENGTH}, "
                f"idle_timeout={settings.CHAT_WIKI_IDLE_TIMEOUT_MINUTES}m)")

    while _RUNNING:
        try:
            await asyncio.sleep(settings.CHAT_WIKI_CHECK_INTERVAL_SECONDS)

            if not settings.CHAT_WIKI_CONVERSION_ENABLED:
                continue

            if reconciliation_gate.is_busy():
                logger.debug("Chat ingest skipped — reconciliation in progress")
                continue

            from src.idle_sentinel import IdleSentinel
            from src.progress_tracker import update as progress_update
            IdleSentinel.update_activity("chat_ingest", True)
            try:
                progress_update("chat_ingest", status="running")
                await process_eligible_conversations()
            finally:
                IdleSentinel.update_activity("chat_ingest", False)
                progress_update("chat_ingest", status="idle")

            _LAST_RUN = datetime.now(timezone.utc).isoformat()

        except asyncio.CancelledError:
            logger.info("Chat ingest scheduler cancelled.")
            break
        except Exception as e:
            logger.error(f"Chat ingest scheduler error: {e}", exc_info=True)

    _RUNNING = False


async def process_eligible_conversations():
    global _CONVERSATIONS_CHECKED, _CONVERSATIONS_INGESTED
    global _PAGES_CREATED, _PAGES_UPDATED

    _ensure_user_page()
    eligible_ids = get_eligible_conversations()
    if not eligible_ids:
        return

    logger.info(f"Checking {len(eligible_ids)} eligible conversations for wiki extraction")

    for cid in eligible_ids:
        _CONVERSATIONS_CHECKED += 1
        meta = get_conversation_meta(cid)

        if meta.get("ingested"):
            remove_eligible_conversation(cid)
            continue

        if not is_conversation_idle(cid):
            continue

        raw = cache_store.get(f"conversation:{cid}")
        if not raw:
            remove_eligible_conversation(cid)
            continue

        messages = raw if isinstance(raw, list) else []
        if len(messages) < settings.CHAT_WIKI_MIN_CONVERSATION_LENGTH * 2:
            continue

        try:
            from src.agents.chat_ingest_agent import ChatIngestAgent
            agent = ChatIngestAgent()
            result = await agent.analyze_conversation(messages, cid)

            pages_created = []
            pages_updated = []

            from src.wiki.writer import write_page, cross_reference_new_page, append_to_index, append_to_log, slugify, invalidate_index_cache, build_index
            from src.knowledge_graph.connection import neo4j_conn
            from src.knowledge_graph.ingest import ingest_wiki_page

            for page in result.get("suggested_pages", []):
                if page.get("confidence", 0) < settings.WIKI_MIN_CONFIDENCE:
                    continue
                if not settings.WIKI_AUTO_CREATE:
                    break

                page_type = page.get("page_type", "entities")
                if page_type not in ("entities", "concepts", "projects"):
                    from src.agents.ingest_agent import IngestAgent
                    base_agent = IngestAgent()
                    page_type = base_agent.classify_page_type(
                        page["title"], page.get("summary", ""), page.get("tags", [])
                    )

                sources = page.get("sources", [])
                if f"conversation:{cid}" not in sources:
                    sources.append(f"conversation:{cid}")

                slug, is_new = write_page(
                    title=page["title"],
                    body=page.get("body", ""),
                    tags=page.get("tags", []),
                    sources=sources,
                    related=page.get("related", []),
                    page_type=page_type,
                )

                try:
                    cross_reference_new_page(slug, page["title"], page_type)
                except Exception as xref_err:
                    logger.warning(f"Cross-reference failed for '{page['title']}': {xref_err}")

                if settings.LAST30DAYS_ENABLED:
                    try:
                        from src.staleness_queue import record_pulse_completed
                        record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
                    except Exception as queue_err:
                        logger.warning(f"Failed to seed staleness queue for '{slug}': {queue_err}")

                try:
                    driver = neo4j_conn.get_driver()
                    full_content = (
                        f"---\ntitle: {page['title']}\ntags: {page.get('tags', [])}\n"
                        f"sources: {sources}\nrelated: {page.get('related', [])}\n---\n\n{page.get('body', '')}"
                    )
                    ingest_wiki_page(driver, title=page["title"], content=full_content)
                except Exception as neo4j_err:
                    logger.warning(f"Neo4j ingest failed for '{page['title']}': {neo4j_err}")

                if is_new:
                    pages_created.append(page["title"])
                else:
                    pages_updated.append(page["title"])

                _increment_reinforcement(slug)
                _apply_adaptive_confidence(slug, page["title"], page_type)

            # Research thread detection
            try:
                threads = _detect_research_threads()
                if threads:
                    logger.info(f"Research threads detected: {threads}")
            except Exception as thread_err:
                logger.warning(f"Research thread detection failed: {thread_err}")

            # Conversation snapshot
            try:
                _save_conversation_snapshot(messages, cid)
            except Exception as snap_err:
                logger.warning(f"Conversation snapshot failed: {snap_err}")

            # Handle name detection
            user_name = result.get("user_name_detected")
            if user_name:
                try:
                    await _handle_user_name_detected(user_name, cid)
                except Exception as name_err:
                    logger.warning(f"Failed to update user name: {name_err}")

            # Handle temporal references
            temporal_refs = result.get("temporal_references", [])
            if temporal_refs:
                try:
                    _create_temporal_events(temporal_refs, cid)
                except Exception as te_err:
                    logger.warning(f"Failed to create temporal events: {te_err}")

            # Update user entity with discussed entities
            entities_discussed = result.get("entities_discussed", [])
            if entities_discussed:
                try:
                    _update_user_entity_interests(entities_discussed)
                except Exception as ue_err:
                    logger.warning(f"Failed to update user entity: {ue_err}")

            # Index and log
            if pages_created or pages_updated:
                index_entries = [
                    (slugify(p["title"]), p["title"], p.get("page_type", "entities"))
                    for p in result.get("suggested_pages", [])
                    if p.get("confidence", 0) >= settings.WIKI_MIN_CONFIDENCE
                ]
                if index_entries:
                    try:
                        append_to_index(index_entries)
                    except Exception as idx_err:
                        logger.warning(f"Index update failed: {idx_err}")

                log_text = (
                    f"Chat ingest of {cid}: {len(pages_created)} pages created, "
                    f"{len(pages_updated)} updated"
                )
                try:
                    append_to_log(log_text)
                except Exception as log_err:
                    logger.warning(f"Log update failed: {log_err}")

                invalidate_index_cache()
                cache_store.invalidate_all()

            # Mark conversation ingested
            update_conversation_meta(cid, {
                "ingested": True,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "pages_created": pages_created,
                "pages_updated": pages_updated,
            })
            remove_eligible_conversation(cid)

            _CONVERSATIONS_INGESTED += 1
            _PAGES_CREATED += len(pages_created)
            _PAGES_UPDATED += len(pages_updated)

            logger.info(f"Ingested conversation {cid}: {len(pages_created)} created, {len(pages_updated)} updated")

        except ImportError:
            logger.debug("ChatIngestAgent not yet available — skipping conversation ingestion")
            break
        except Exception as e:
            logger.error(f"Failed to process conversation {cid}: {e}", exc_info=True)


def _ensure_user_page():
    from src.wiki.writer import read_page, write_page, slugify
    slug = slugify(settings.CHAT_WIKI_USER_ENTITY_NAME)
    existing = read_page(slug, page_type="entities")
    if existing:
        return existing
    body = (
        f"## Summary\n\n"
        f"This is the wiki entity for the user of Project Chicken Soup. "
        f"The system will track research interests, frequently discussed "
        f"entities, and conversation history here.\n\n"
        f"## Research Interests\n\n"
        f"_(Interests will appear as the user discusses topics with the AI)_\n\n"
        f"## Conversation History\n\n"
        f"_(Conversation history will be recorded automatically)_\n"
    )
    write_page(
        title=settings.CHAT_WIKI_USER_ENTITY_NAME,
        body=body,
        tags=["person", "user"],
        sources=["chat-system"],
        related=[],
        page_type="entities",
    )
    return read_page(slug, page_type="entities")


async def _handle_user_name_detected(detected_name: str, conversation_id: str):
    from src.wiki.writer import read_page, write_page, slugify, append_to_index
    from src.config import settings

    current_name = settings.CHAT_WIKI_USER_ENTITY_NAME
    current_slug = slugify(current_name)
    new_slug = slugify(detected_name)

    existing = read_page(current_slug, page_type="entities")
    if not existing:
        existing = _ensure_user_page()
    if not existing:
        return

    frontmatter = existing["frontmatter"]
    body = existing["body"]

    related = frontmatter.get("related", [])
    if f"conversation:{conversation_id}" not in frontmatter.get("sources", []):
        sources = frontmatter.get("sources", []) + [f"conversation:{conversation_id}"]
    else:
        sources = frontmatter.get("sources", [])

    if new_slug != current_slug:
        write_page(
            title=detected_name,
            body=body,
            tags=frontmatter.get("tags", ["person", "user"]),
            sources=sources,
            related=related,
            page_type="entities",
        )
        try:
            from src.wiki.writer import delete_page
            delete_page(current_slug, page_type="entities")
        except Exception:
            pass

        try:
            append_to_index([(new_slug, detected_name, "entities")])
        except Exception:
            pass
    else:
        write_page(
            title=detected_name,
            body=body,
            tags=frontmatter.get("tags", ["person", "user"]),
            sources=sources,
            related=related,
            page_type="entities",
        )


def _create_temporal_events(temporal_refs: list, conversation_id: str):
    from src.knowledge_graph.connection import neo4j_conn
    from src.knowledge_graph.ingest import ingest_wiki_page
    from src.wiki.writer import write_page, cross_reference_new_page

    driver = neo4j_conn.get_driver()
    if not driver:
        return

    for ref in temporal_refs:
        title = ref.get("event", "Unknown Event")
        description = ref.get("description", f"Extracted from conversation {conversation_id}")
        date_str = ref.get("date", "")
        tags = ["event", "temporal-reference"]
        sources = [f"conversation:{conversation_id}"]

        body = description.strip()
        if date_str:
            body += f"\n\n**Date:** {date_str}"

        # Write a wiki page so the event becomes a first-class entity with full LLM pipeline
        slug, is_new = write_page(
            title=title,
            body=body,
            tags=tags,
            sources=sources,
            related=[],
            page_type="entities",
        )
        try:
            cross_reference_new_page(slug, title, "entities")
        except Exception as xref_err:
            logger.warning(f"Cross-reference failed for temporal event '{title}': {xref_err}")

        # Ingest to Neo4j through the full pipeline (LLM edge classification)
        full_content = (
            f"---\ntitle: {title}\ntags: {tags}\nsources: {sources}\nrelated: []\n---\n\n{body}"
        )
        try:
            ingest_wiki_page(driver, title=title, content=full_content)
        except Exception as neo4j_err:
            logger.warning(f"Neo4j ingest failed for temporal event '{title}': {neo4j_err}")


def _update_user_entity_interests(entities_discussed: list):
    from src.wiki.writer import read_page, write_page, slugify

    user_slug = slugify(settings.CHAT_WIKI_USER_ENTITY_NAME)
    existing = read_page(user_slug, page_type="entities")
    if not existing:
        return

    frontmatter = existing["frontmatter"]
    body = existing["body"]
    existing_related = set(frontmatter.get("related", []))
    new_related = list(existing_related | set(entities_discussed))

    interests_section = "## Research Interests\n"
    for entity in sorted(set(entities_discussed)):
        interest_line = f"- {entity}\n"
        if interest_line not in body:
            body += interest_line

    write_page(
        title=frontmatter.get("title", settings.CHAT_WIKI_USER_ENTITY_NAME),
        body=body,
        tags=frontmatter.get("tags", ["person", "user"]),
        sources=frontmatter.get("sources", []),
        related=new_related,
        page_type="entities",
    )


# ── Phase 5.1: Research Thread Detection ─────────────────────────

def _get_all_ingested_topics() -> dict:
    from src.wiki.writer import read_page, slugify
    user_slug = slugify(settings.CHAT_WIKI_USER_ENTITY_NAME)
    user_page = read_page(user_slug, page_type="entities")
    if not user_page:
        return {}

    body = user_page["body"]
    conversation_blocks = re.split(r"^- \[", body, flags=re.MULTILINE)
    topics_per_conv: dict = {}
    current_conv = None

    for block in conversation_blocks:
        if not block.strip():
            continue
        date_match = re.match(r"^(\d{4}-\d{2}-\d{2})\]\s*(.*)", block)
        if date_match:
            current_conv = date_match.group(0).strip()
            topics_per_conv[current_conv] = set()
        if current_conv:
            entity_links = re.findall(r"\[\[([^\]]+)\]\]", block)
            topics_per_conv[current_conv].update(entity_links)
            capitalized = re.findall(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", block)
            for word in capitalized:
                if len(word) > 3 and word not in ("This", "The", "What", "When", "Where", "How", "From", "With", "That", "Have", "Been", "Would", "Could", "Should", "About", "Also", "Your", "They", "Were", "There", "Their", "These", "Those", "Which"):
                    topics_per_conv[current_conv].add(word)

    return topics_per_conv


def _detect_research_threads() -> List[str]:
    topics_per_conv = _get_all_ingested_topics()
    if len(topics_per_conv) < 3:
        return []

    all_entities: dict = {}
    for conv, entities in topics_per_conv.items():
        for entity in entities:
            all_entities.setdefault(entity, []).append(conv)

    recurring = {e: convs for e, convs in all_entities.items() if len(convs) >= 3}
    if not recurring:
        return []

    from src.wiki.writer import read_page, slugify
    recurring = dict(sorted(recurring.items(), key=lambda x: -len(x[1])))
    primary_topic = next(iter(recurring))
    thread_slug = f"research-thread-{slugify(primary_topic)}"
    existing = read_page(thread_slug, page_type="projects")
    if existing:
        return []

    body_parts = [
        f"## Research Thread: {primary_topic}\n",
        f"This thread was automatically detected from multiple conversations "
        f"where **{primary_topic}** was discussed.\n",
        f"## Related Conversations\n",
    ]
    related_entities = set()
    for conv in recurring[primary_topic]:
        related_entities.update(topics_per_conv.get(conv, set()))
        body_parts.append(f"- {conv}\n")
    body_parts.append(f"\n## Related Entities\n")
    for entity in sorted(related_entities):
        body_parts.append(f"- [[{entity}]]\n")
    body_parts.append(
        f"\n## Key Findings\n\n"
        f"_This is an auto-generated research thread page. "
        f"Key findings will be populated as conversations continue._\n"
    )

    from src.wiki.writer import write_page, append_to_index, append_to_log, slugify as wslug
    slug, is_new = write_page(
        title=f"Research Thread: {primary_topic}",
        body="".join(body_parts),
        tags=["research-thread", "auto-detected", slugify(primary_topic)],
        sources=["chat-system"],
        related=list(related_entities),
        page_type="projects",
    )
    if is_new:
        try:
            append_to_index([(slug, f"Research Thread: {primary_topic}", "projects")])
            append_to_log(f"Research thread created: {primary_topic} ({len(recurring[primary_topic])} conversations)")
        except Exception:
            pass
        logger.info(f"Research thread created: {primary_topic}")
    return [primary_topic]


# ── Phase 5.2: Adaptive Confidence ──────────────────────────────

def _reinforcement_key(slug: str) -> str:
    return f"reinforcement:{slug}"


def _increment_reinforcement(slug: str):
    if not cache_store.redis_client:
        return
    try:
        cache_store.redis_client.incr(_reinforcement_key(slug))
        cache_store.redis_client.expire(_reinforcement_key(slug), 2592000)
    except Exception:
        pass


def _get_reinforcement_count(slug: str) -> int:
    if not cache_store.redis_client:
        return 0
    try:
        val = cache_store.redis_client.get(_reinforcement_key(slug))
        return int(val) if val else 0
    except Exception:
        return 0


def _apply_adaptive_confidence(slug: str, page_title: str, page_type: str):
    count = _get_reinforcement_count(slug)
    if count < 2:
        return

    from src.wiki.writer import read_page, write_page
    existing = read_page(slug, page_type)
    if not existing:
        return

    fm = existing["frontmatter"]
    body = existing["body"]
    confidence_str = f"*Confidence: reinforced {count}x across conversations*"
    if confidence_str not in body:
        body += f"\n\n{confidence_str}\n"

    write_page(
        title=fm.get("title", page_title),
        body=body,
        tags=fm.get("tags", []),
        sources=fm.get("sources", []),
        related=fm.get("related", []),
        page_type=page_type,
    )
    logger.info(f"Adaptive confidence: {page_title} reinforced {count}x")


# ── Phase 5.3: Conversation Snapshots ───────────────────────────

def _save_conversation_snapshot(messages: list, conversation_id: str):
    raw_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "wiki", "raw"
    )
    os.makedirs(raw_dir, exist_ok=True)

    today = date.today().isoformat()
    safe_id = conversation_id.replace(":", "-").replace("/", "-")
    filename = f"conversation-{safe_id}-{today}.md"
    filepath = os.path.join(raw_dir, filename)

    meta = {
        "title": f"Conversation {conversation_id[:8]}",
        "tags": ["conversation", "chat-archive"],
        "created": today,
        "updated": today,
        "sources": [f"conversation:{conversation_id}"],
        "related": [],
    }
    yaml_str = "---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n\n"

    body_parts = [yaml_str]
    body_parts.append(f"# Conversation Snapshot\n\n")
    body_parts.append(f"**ID:** `{conversation_id}`  \n")
    body_parts.append(f"**Date:** {today}  \n")
    body_parts.append(f"**Messages:** {len(messages)}\n\n")

    user_count = sum(1 for m in messages if m.get("role") == "user")
    assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
    body_parts.append(f"**User turns:** {user_count}  \n")
    body_parts.append(f"**Assistant turns:** {assistant_count}\n\n---\n\n")

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        prefix = "**User:**" if role == "user" else "**Assistant:**"
        body_parts.append(f"### Message {i+1} ({role})\n\n{prefix} {content}\n\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(body_parts))
    logger.info(f"Conversation snapshot saved: {filepath}")


# ── Phase 5.4: Granular Notifications ───────────────────────────

def get_ingest_history(limit: int = 20) -> List[dict]:
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "wiki", "log.md"
    )
    if not os.path.isfile(log_path):
        return []

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    from src.wiki.writer import parse_frontmatter
    md = parse_frontmatter(content)
    body = md["body"]

    entries = []
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("## [") and "ingest" in line:
            date_match = re.match(r"## \[(\d{4}-\d{2}-\d{2})\]\s*(\w+)\s*\|\s*(.*)", line)
            if date_match:
                entries.append({
                    "date": date_match.group(1),
                    "type": date_match.group(2),
                    "description": date_match.group(3),
                })
    return entries[:limit]


def get_recent_notifications(limit: int = 10) -> List[dict]:
    history = get_ingest_history(limit)
    notifications = []
    for entry in history:
        if "chat ingest" in entry["description"].lower():
            page_match = re.search(r"(\d+) pages? created", entry["description"])
            pages_created = int(page_match.group(1)) if page_match else 0
            notifications.append({
                "date": entry["date"],
                "type": "chat_ingest",
                "description": entry["description"],
                "pages_created": pages_created,
            })
    return notifications[:limit]


# ── Phase 6: Idle-Driven Ingestion Loop ──────────────────────────────────

_IDLE_INGESTION_RUNNING = False
_IDLE_LAST_RUN: Optional[str] = None
_IDLE_CHECK_INTERVAL_SECONDS = 30  # check every 30s (Phase 7: reduced polling)
_IDLE_CONSECUTIVE_IDENTICAL_BATCHES = 0
_IDLE_LAST_BATCH: Optional[List[str]] = None

async def idle_ingestion_loop():
    global _IDLE_INGESTION_RUNNING, _IDLE_LAST_RUN
    global _IDLE_CONSECUTIVE_IDENTICAL_BATCHES, _IDLE_LAST_BATCH

    _IDLE_INGESTION_RUNNING = True
    logger.info("Idle-driven ingestion loop started")

    while _IDLE_INGESTION_RUNNING:
        try:
            await asyncio.sleep(_IDLE_CHECK_INTERVAL_SECONDS)

            if not settings.LAST30DAYS_ENABLED:
                continue

            if not settings.LAST30DAYS_PULSE_ENABLED:
                progress_update("idle_ingestion", status="pulsing_disabled")
                if _IDLE_CONSECUTIVE_IDENTICAL_BATCHES > 0:
                    _IDLE_CONSECUTIVE_IDENTICAL_BATCHES = 0
                await asyncio.sleep(60)
                continue

            from src.idle_sentinel import IdleSentinel
            from src.staleness_queue import get_next_batch, record_pulse_completed
            from src.agents.pulse_agent import PulseAgent
            from src.progress_tracker import update as progress_update, increment as progress_inc

            if not IdleSentinel.is_idle():
                continue

            if reconciliation_gate.is_busy():
                logger.debug("Idle ingestion skipped — reconciliation in progress")
                continue

            # Get highest priority entity slugs
            batch = get_next_batch(1)  # Phase 7: one pulse at a time when idle
            if not batch:
                _IDLE_CONSECUTIVE_IDENTICAL_BATCHES = 0
                _IDLE_LAST_BATCH = None
                continue

            # Detect consecutive identical batches (orphan spin)
            if _IDLE_LAST_BATCH is not None and batch == _IDLE_LAST_BATCH:
                _IDLE_CONSECUTIVE_IDENTICAL_BATCHES += 1
                if _IDLE_CONSECUTIVE_IDENTICAL_BATCHES >= 5:
                    logger.error(
                        f"Same batch returned {_IDLE_CONSECUTIVE_IDENTICAL_BATCHES}x consecutively — "
                        f"orphaned slugs detected: {batch}. Run rebuild_queue() or check staleness queue."
                    )
            else:
                _IDLE_CONSECUTIVE_IDENTICAL_BATCHES = 0
            _IDLE_LAST_BATCH = batch

            logger.info(f"Idle ingestion loop processing batch: {batch}")
            pulse_agent = PulseAgent()
            progress_update("idle_ingestion", status="pulsing")

            for slug in batch:
                # Cooperative yielding: check idle state before processing each entity
                if not IdleSentinel.is_idle():
                    logger.info("Ingestion preempted by system activity, yielding loop.")
                    break

                try:
                    from src.wiki.writer import read_page
                    page_data = read_page(slug)
                    if not page_data or "frontmatter" not in page_data:
                        logger.warning(f"Page '{slug}' not found on disk — removing from staleness queue")
                        if cache_store.redis_client:
                            cache_store.redis_client.zrem("staleness:queue", slug)
                        continue
                    
                    entity_name = page_data["frontmatter"].get("title", slug)

                    # Skip pulse for engineering-only pages (no content tags)
                    tags = page_data["frontmatter"].get("tags", [])
                    from src.wiki.cleanup import ENGINEERING_TAGS, CONTENT_TAGS
                    tag_set = set(str(t) for t in tags)
                    is_engineering = bool(tag_set & ENGINEERING_TAGS)
                    has_content = bool(tag_set & CONTENT_TAGS)
                    if is_engineering and not has_content:
                        logger.info(f"Skipping pulse for engineering page '{slug}'")
                        record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
                        _IDLE_LAST_RUN = datetime.now(timezone.utc).isoformat()
                        continue

                    logger.info(f"Running idle pulse for '{entity_name}'")
                    progress_update("idle_ingestion", status="pulsing", current_slug=slug)
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, pulse_agent.run_pulse, entity_name)
                    
                    # Compute divergence risk & state label if we got evidence
                    div_risk = 0.0
                    state_label = "unverified"
                    if result.evidence:
                        from src.quantum_credibility.divergence_engine import compute_narrative_divergence
                        div_res = compute_narrative_divergence(entity_name, page_data, result.evidence)
                        div_risk = div_res.divergence_risk
                        
                        from src.quantum_credibility.wavefunction import ClaimWavefunction
                        wf = ClaimWavefunction()
                        claim_text = page_data["body"][:5000] if page_data.get("body") else entity_name
                        
                        rc = _get_reinforcement_count(slug)
                        cc = wf.score_claim(claim_text, result.evidence, reinforcement_count=rc)
                        state_label = cc.state_label

                    # Optional: enrich chat-created wiki pages with external evidence
                    if result.evidence:
                        sources = page_data.get("frontmatter", {}).get("sources", [])
                        is_chat_created = any(isinstance(s, str) and s.startswith("conversation:") for s in sources)
                        if is_chat_created:
                            try:
                                from src.wiki.writer import write_page
                                top_claims = sorted(
                                    result.evidence,
                                    key=lambda ev: ev.engagement_count if hasattr(ev, "engagement_count") else 0,
                                    reverse=True
                                )[:3]
                                evidence_section = "\n\n## External Evidence\n\n"
                                for ev in top_claims:
                                    claim_text = getattr(ev, "claim_text", "") or ""
                                    if claim_text:
                                        evidence_section += f"- {claim_text}\n"
                                if len(evidence_section) > len("\n\n## External Evidence\n\n"):
                                    updated_body = page_data.get("body", "") + evidence_section
                                    write_page(
                                        title=page_data["frontmatter"].get("title", entity_name),
                                        body=updated_body,
                                        tags=page_data["frontmatter"].get("tags", []),
                                        sources=sources,
                                        related=page_data["frontmatter"].get("related", []),
                                        page_type=page_data.get("page_type", "entities"),
                                    )
                                    logger.info(f"Enriched wiki page '{slug}' with {len(top_claims)} external evidence items")
                            except Exception as enrich_err:
                                logger.warning(f"Wiki page enrichment failed for '{slug}': {enrich_err}")

                    record_pulse_completed(slug, divergence_risk=div_risk, state_label=state_label)
                    _IDLE_LAST_RUN = datetime.now(timezone.utc).isoformat()
                    status_label = getattr(result, "status", "unknown") if result else "error"
                    if status_label == "success":
                        progress_inc("idle_ingestion", "pulses_success")
                    else:
                        progress_inc("idle_ingestion", "pulses_error")
                    progress_update("idle_ingestion", last_result=status_label, last_run=_IDLE_LAST_RUN)

                except Exception as ent_err:
                    logger.error(f"Error processing entity '{slug}' in idle loop: {ent_err}", exc_info=True)
                    progress_inc("idle_ingestion", "pulses_error")

        except asyncio.CancelledError:
            logger.info("Idle-driven ingestion loop cancelled")
            break
        except Exception as e:
            logger.error(f"Idle-driven ingestion loop error: {e}", exc_info=True)

    _IDLE_INGESTION_RUNNING = False


async def rebuild_queue_daily_loop():
    """Calls rebuild_queue() every 24 hours to sync Redis with the filesystem."""
    logger.info("Daily queue rebuild loop started (24h interval)")
    while True:
        try:
            await asyncio.sleep(86400)
            from src.staleness_queue import rebuild_queue
            rebuild_queue()
            logger.info("Daily staleness queue rebuild complete")
        except asyncio.CancelledError:
            logger.info("Daily queue rebuild loop cancelled")
            break
        except Exception as e:
            logger.warning(f"Daily queue rebuild failed: {e}")


def get_almanac_status() -> dict:
    return {
        "enabled": settings.LAST30DAYS_ENABLED,
        "last_run": _IDLE_LAST_RUN,
        "running": _IDLE_INGESTION_RUNNING,
    }


_FALLBACK_RETRY_RUNNING = False


async def fallback_retry_loop():
    """Periodically retry LLM extraction for fallback-tagged pages.
    Pops one slug per cycle from the Redis retry queue, re-runs entity
    extraction via the LLM. On success, updates the Neo4j node to clear
    the fallback flag. Runs only when the system is idle."""
    global _FALLBACK_RETRY_RUNNING
    _FALLBACK_RETRY_RUNNING = True
    logger.info("Fallback retry loop started (1h interval)")

    while _FALLBACK_RETRY_RUNNING:
        try:
            await asyncio.sleep(3600)

            from src.idle_sentinel import IdleSentinel
            from src.reconciliation_gate import reconciliation_gate
            from src.progress_tracker import update as progress_update, increment as progress_inc

            if not IdleSentinel.is_idle() or reconciliation_gate.is_busy():
                continue

            if not cache_store.redis_client:
                continue

            queue_size = cache_store.redis_client.scard("retry:fallback")
            slug = cache_store.redis_client.spop("retry:fallback")
            if not slug:
                continue

            progress_update("fallback_retry", status="retrying", current_slug=slug, queue_size=str(queue_size))

            from src.wiki.writer import read_page
            page_data = read_page(slug)
            if not page_data or "frontmatter" not in page_data:
                continue

            title = page_data["frontmatter"].get("title", slug)
            body = page_data.get("body", "")

            from src.agents.ingest_agent import IngestAgent
            from src.knowledge_graph.connection import neo4j_conn
            from src.knowledge_graph.ingest import ingest_wiki_page

            agent = IngestAgent()
            analysis = agent.analyze_content(body, filename=f"{slug}.md")

            if analysis and analysis.confidence >= 0.5:
                sources = page_data["frontmatter"].get("sources", [])
                tags = page_data["frontmatter"].get("tags", [])
                tags = [t for t in tags if t != "fallback"]
                related = page_data["frontmatter"].get("related", [])

                from src.wiki.writer import write_page
                from src.knowledge_graph.ingest import _seed_fallback_retry
                analysis_result = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis
                body = analysis_result.get("body", body)
                write_page(title=title, body=body, tags=tags, sources=sources, related=related, page_type=page_data.get("page_type", "entities"))

                content = f"---\ntitle: {title}\ntags: {tags}\nsources: {sources}\nrelated: {related}\n---\n\n{body}"
                driver = neo4j_conn.get_driver()
                if driver:
                    ingest_wiki_page(driver, title=title, content=content, default_tags=tags, default_sources=sources)

                _seed_fallback_retry(slug)

                logger.info(f"Fallback retry succeeded for '{slug}'")
                progress_inc("fallback_retry", "succeeded")
                progress_update("fallback_retry", status="idle", last_result="success",
                    last_run=datetime.now(timezone.utc).isoformat())
            else:
                cache_store.redis_client.sadd("retry:fallback", slug)
                cache_store.redis_client.expire("retry:fallback", 2592000)
                logger.debug(f"Fallback retry failed for '{slug}', re-queued")
                progress_inc("fallback_retry", "failed")
                progress_update("fallback_retry", status="idle", last_result="failed",
                    last_run=datetime.now(timezone.utc).isoformat())

        except asyncio.CancelledError:
            logger.info("Fallback retry loop cancelled")
            break
        except Exception as e:
            logger.warning(f"Fallback retry loop error: {e}", exc_info=True)
            progress_update("fallback_retry", status="error", last_error=str(e)[:200])

    _FALLBACK_RETRY_RUNNING = False


def stop():
    global _RUNNING, _IDLE_INGESTION_RUNNING, _FALLBACK_RETRY_RUNNING, _NEO4J_BACKUP_RUNNING
    _RUNNING = False
    _IDLE_INGESTION_RUNNING = False
    _FALLBACK_RETRY_RUNNING = False
    _NEO4J_BACKUP_RUNNING = False


_NEO4J_BACKUP_RUNNING = True

async def neo4j_backup_loop():
    """Periodically create Neo4j database dumps. Runs on configurable interval."""
    global _NEO4J_BACKUP_RUNNING
    _NEO4J_BACKUP_RUNNING = True
    interval = settings.NEO4J_BACKUP_INTERVAL_HOURS * 3600
    logger.info(f"Neo4j backup loop started ({settings.NEO4J_BACKUP_INTERVAL_HOURS}h interval)")

    while _NEO4J_BACKUP_RUNNING:
        try:
            await asyncio.sleep(interval)

            from src.neo4j_backup import create_backup, cleanup_old_backups, list_backups
            from src.progress_tracker import update as progress_update

            path = create_backup()
            if path:
                logger.info(f"Neo4j backup created: {path}")
                deleted = cleanup_old_backups()
                if deleted:
                    logger.info(f"Cleaned up {deleted} old Neo4j backups")

                backups = list_backups()
                latest = backups[0] if backups else {}
                progress_update("neo4j_backup", status="ok", last_backup=latest.get("filename", ""),
                                total_backups=str(len(backups)))
            else:
                logger.warning("Neo4j backup failed")
                progress_update("neo4j_backup", status="error")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Neo4j backup error: {e}")

    _NEO4J_BACKUP_RUNNING = False
