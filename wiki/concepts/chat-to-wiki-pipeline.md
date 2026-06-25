---
title: "Chat-to-Wiki Pipeline"
tags: [chat, ingest, scheduler, wiki, automation]
created: 2026-06-25
updated: 2026-06-25
sources: [chat-system]
related: [ingestion-pipeline, wiki-file-system, agent-architecture, api-design, conversation-entity-management]
---

# Chat-to-Wiki Pipeline

A periodic background system that converts user–AI conversations into wiki pages automatically. Every 5 minutes, the scheduler checks for eligible conversations, runs them through a chat-specific LLM agent, and creates/updates wiki pages with extracted entities, concepts, and projects.

## Architecture

```
[User Chat] → POST /query → Redis conversation:{id} [messages + meta]
                                    │
                    ┌───────────────┴───────────────┐
                    │   (every 300s)                 │
                    ▼                                ▼
          scheduler.py ────► ChatIngestAgent ────► write_page()
                    │                                │
                    ▼                                ▼
          cross_reference_new_page() ────► ingest_wiki_page() → Neo4j
                                                    │
                                                    ▼
          append_to_index() + append_to_log() + invalidate_cache()
```

## Components

### Scheduler (`src/scheduler.py`, ~465 lines)

- **Periodic loop**: Runs every `CHAT_WIKI_CHECK_INTERVAL_SECONDS` (default 300), gated by `CHAT_WIKI_CONVERSION_ENABLED` (default False — opt-in)
- **Eligibility detection**: Conversations must have `message_count >= CHAT_WIKI_MIN_CONVERSATION_LENGTH` (default 10) AND be idle for `CHAT_WIKI_IDLE_TIMEOUT_MINUTES` (default 30)
- **Idempotency**: Each conversation's `meta` has an `ingested` flag; once processed it is removed from the `conversation:eligible` Redis set
- **Tracking**: Redis keys `conversation:{id}:meta` store `message_count`, `last_activity`, `ingested`, `pages_created`, `pages_updated` with 7-day TTL
- **Manual trigger**: `POST /chat/ingest/now` runs an immediate scan

### ChatIngestAgent (`src/agents/chat_ingest_agent.py`, 208 lines)

- **Conversation-specific prompt**: Handles Q&A format (not document format). Extracts entities, concepts, projects, user name, temporal references
- **User name detection**: LLM prompt includes the current user entity name; if user reveals their name, `user_name_detected` is returned
- **Temporal extraction**: Detects date/event references for Neo4j Event nodes
- **Fallback analysis**: When LLM is unavailable, extracts capitalized words as candidate entities with 0.4 confidence
- **Deduplication**: LLM prompt includes existing wiki index (200 pages) to avoid creating duplicate pages

### Conversation Meta (Redis)

Each conversation stores two keys:
- `conversation:{id}` — Full message history (JSON array, last 20 turns, 7-day TTL)
- `conversation:{id}:meta` — Metadata dict: `message_count`, `last_activity`, `ingested`, `ingested_at`, `pages_created`

An auxiliary Redis Set `conversation:eligible` tracks IDs that meet the minimum message threshold for quick iteration.

### User Entity Management

- On first run, `entities/primary-researcher.md` is auto-created with tags `[person, user]`
- When the LLM detects the user revealing their name, the scheduler renames the entity page and updates all cross-references
- User can manually set name via `POST /chat/name`
- Research interests are accumulated on the user page after each conversation ingest

## Advanced Features

### Research Thread Detection

After each ingest, the scheduler parses the user entity's conversation history. If a topic appears across 3+ distinct conversations, a `projects/research-thread-{topic}.md` page is auto-created with a summary of related entities and conversations.

### Adaptive Confidence

Redis counters (`reinforcement:{slug}`) track how many times a topic is discussed. After 2+ reinforcements, the page body gains a note: "*Confidence: reinforced Nx across conversations*".

### Conversation Snapshots

After each successful ingest, the full message history is saved as an immutable markdown file to `wiki/raw/conversation-{id}-{date}.md` with YAML frontmatter, turn counts, and full message text.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/conversations` | List all conversations with meta |
| `GET` | `/conversation/{id}` | Retrieve full conversation history |
| `GET` | `/chat/ingest/status` | Scheduler status (last run, counts) |
| `POST` | `/chat/ingest/now` | Trigger immediate scan |
| `GET` | `/chat/ingest/history` | Recent ingest events from wiki log |
| `GET` | `/chat/ingest/notifications` | Chat-specific ingest notifications |
| `POST` | `/chat/name` | Set or rename user wiki entity |

## Configuration

All settings in `src/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `CHAT_WIKI_CONVERSION_ENABLED` | `False` | Master switch (opt-in) |
| `CHAT_WIKI_MIN_CONVERSATION_LENGTH` | `10` | Minimum messages before eligibility |
| `CHAT_WIKI_CHECK_INTERVAL_SECONDS` | `300` | How often the scheduler checks |
| `CHAT_WIKI_IDLE_TIMEOUT_MINUTES` | `30` | How long a conversation must be idle |
| `CHAT_WIKI_USER_ENTITY_NAME` | `Primary Researcher` | Initial user wiki entity name |

## See Also

- [[ingestion-pipeline]]
- [[wiki-file-system]]
- [[agent-architecture]]
- [[conversation-entity-management]]
