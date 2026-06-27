---
title: "Wiki File System"
tags: [wiki, files, markdown, frontmatter, crud]
created: 2026-06-25
updated: 2026-06-25
sources: [project-structure-2026-06-22]
related: [ingestion-pipeline, chat-to-wiki-pipeline, knowledge-graph-ingestion, project-structure]
---

# Wiki File System

The wiki is a file‑based Obsidian‑compatible markdown vault at `wiki/`. All pages use YAML frontmatter with cross‑references via `[[wikiname]]` syntax. The `src/wiki/writer.py` module (241 lines) provides CRUD operations, index management, and bidirectional cross‑referencing.

## Directory Structure

```
wiki/
├── index.md          # Content catalog (updated on every ingest)
├── log.md            # Append-only chronological log
├── overview.md       # Top-level summary
├── entities/         # 78 pages — people, places, objects, events
├── concepts/         # 91 pages — ideas, theories, frameworks
├── projects/         # 6 pages — engineering, architecture
└── raw/              # Immutable source documents, conversation snapshots
```

## Page Format

Every page uses YAML frontmatter:

```yaml
---
title: "Page Title"
tags: [ufo, time-travel, ai]
created: 2026-06-22
updated: 2026-06-25
sources: [conversation:{id}, uploaded-document]
related: [existing-wiki-page]
---
```

## CRUD Operations

### `read_page(slug, page_type)` → `{frontmatter, body, path}`
Parses YAML frontmatter via regex + `yaml.safe_load`. Returns `None` if file does not exist.

### `write_page(title, body, tags, sources, related, page_type)` → `(slug, is_new)`

**Merge semantics** for existing pages:
- `tags` — Set union (existing + new)
- `sources` — Set union
- `related` — Set union
- `body` — Appended: `existing_body + "\n\n" + new_body`
- `created` — Preserved from original
- `updated` — Always set to today

### `delete_page(slug, page_type)` → `bool`
Removes the file from disk.

## Cross‑Referencing

### `cross_reference_new_page(slug, display_name, page_type)`
Scans every `.md` file across all three subdirectories for case‑insensitive mentions of the new slug or display name. When found, adds the new page to the existing page's `related` frontmatter list and updates its `updated` date. This ensures bidirectional links: if `Page A` links to `Page B`, `Page B`'s frontmatter automatically gains `Page A` in its `related` field.

### `lookup_entity(query)` → `[str]`
Fuzzy‑match query words against the wiki index, returning up to 5 matches sorted by relevance score. Used by IngestAgent and QueryAgent for entity disambiguation.

## Index Management

### `build_index()` → `{lower_filename: display_name}`
Scans all `.md` files in all three subdirectories. Builds mappings for both filename‑stem and display‑name forms (e.g., `"bob-lazar"` → `"Bob Lazar"` AND `"bob lazar"` → `"Bob Lazar"`).

### `get_wiki_index()` → cached dict
Module‑level in‑memory cache on the function object. Invalidated via `invalidate_index_cache()` after any write operation.

### `append_to_index(slugs)`
Inserts `[[PageName]]` bullet entries into `wiki/index.md` under the correct section header (`## Entities`, `## Concepts`, `## Projects`). Skips duplicates.

### `append_to_log(entry_text)`
Appends `## [YYYY-MM-DD] ingest | <entry_text>` to `wiki/log.md`.

## Source Attribution

Pages created from chat ingests include the conversation ID in `sources`: `["conversation:{id}"]`. Pages created from file uploads include the original filename. This provides full provenance for every piece of wiki content.

## Key Design Decisions

- **Flat files, not a database**: The wiki is directly browsable in Obsidian, editable by hand, and versioned in git. No separate wiki database is needed.
- **Obsidian‑compatible**: `[[wikiname]]` links render natively in Obsidian. The YAML frontmatter supports Obsidian plugins like Dataview.
- **Monotonic body growth**: Re‑ingesting the same source appends new content rather than replacing it. Dedup is handled at the paragraph level by the LLM extraction prompt, not by the writer.
- **Push‑based cross‑referencing**: Only new pages trigger backlink updates. A full reconciliation pass is not performed — orphan detection is done by linting.

## See Also

- [[ingestion-pipeline]]
- [[chat-to-wiki-pipeline]]
- [[knowledge-graph-ingestion]]
- [[project-structure]]
