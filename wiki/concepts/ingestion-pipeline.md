---
created: 2026-06-25
protected: true
related:
- wiki-file-system
- chat-to-wiki-pipeline
- agent-architecture
- api-design
- knowledge-graph-ingestion
sources:
- project-structure-2026-06-22
tags:
- ingest
- files
- folders
- upload
- wiki
title: Ingestion Pipeline
updated: '2026-06-25'
---

# Ingestion Pipeline

The classic file/folder ingestion pipeline — the original wiki-building mechanism predating chat-to-wiki. Users upload `.txt`, `.md`, `.json`, `.csv` files (or entire folders on macOS) and the AI analyzes them, extracts entities/concepts/projects, and commits them to the wiki + Neo4j.

## Flow

```
File/Folder Upload (SwiftUI DataIngestionView)
       │
       ▼
POST /ingest/analyze  ───►  IngestAgent.analyze_content()
       │                           │
       │                     LLM extraction prompt
       │                     (includes existing wiki index)
       │                           │
       ▼                           ▼
  Preview Cards               SuggestedPage[]
  (user reviews)                  │
       │                          ▼
       │                   Confidence ≥ WIKI_MIN_CONFIDENCE?
       │                    ┌────┴────┐
       │                   YES       NO (skipped)
       │                    │
       ▼                    ▼
POST /ingest/file ────►  write_page() + cross_reference_new_page()
  (or commit button)              │
                                 ▼
                          ingest_wiki_page() → Neo4j
                                 │
                                 ▼
                          append_to_index() + append_to_log()
```

## Components

### IngestAgent (`src/agents/ingest_agent.py`, 182 lines)

- **`analyze_content(text, filename)`** — Sends raw text to LLM with a JSON schema prompt. Returns 1-5 `SuggestedPage` objects with title, page_type, tags, sources, summary, body (markdown), related wiki links, and confidence score (0.0–1.0)
- **Existing wiki dedup**: The LLM prompt includes the first 200 entries from `build_index()` to avoid creating pages for topics already covered
- **Confidence thresholding**: Pages with `confidence < WIKI_MIN_CONFIDENCE` (default 0.5) are skipped
- **`WIKI_AUTO_CREATE` gate**: When disabled, analysis still runs but no pages are written
- **Fallback analysis** (`_fallback_analysis`): When LLM is unavailable, heuristic extraction uses the filename as the title and generates a basic page with 0.4 confidence
- **Page type classification** (`classify_page_type`): Keyword-based detection (person/place/object/event → entities, project/engineering → projects, everything else → concepts)

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/ingest/analyze` | Analyze content → preview (no commit) |
| `POST` | `/ingest/file` | Upload single file → analyze + commit |
| `POST` | `/ingest/folder` | Upload zip → process all files |
| `POST` | `/ingest/bulk` | Clear Neo4j + re-ingest all wiki pages |
| `POST` | `/ingest` | Ingest raw content by title/content (Celery or sync) |

### SwiftUI Frontend (`DataIngestionView.swift`, 1090 lines)

- **Platform‑conditional file importer**:
  - **macOS**: `.folder` picker → enumerate `.txt`/`.md`/`.json`/`.csv` → `POST /ingest/file` per file
  - **iOS**: `.data`/`.zip` multi-select → route by extension (single files → analyze preview, zips → `POST /ingest/folder`)
- **2‑step UX**: Upload → AI analysis preview (entity cards with type/tags/confidence/related) → "Commit to Wiki" → results
- **Drag‑and‑drop**: Also routes through `handleSelectedURLs`
- **Stats dashboard**: Average confidence, total entities, sync queue size
- **Chat Contributions section**: Shows chat-to-wiki ingest status, recent contributions

### `_process_ingested_content()` (`src/main.py:596-683`)

The core pipeline function:
1. `IngestAgent.analyze_content()` extracts pages
2. Per page: confidence gate → page type classification → `write_page()` → `cross_reference_new_page()` → `ingest_wiki_page()` (Neo4j)
3. Batch: `append_to_index()` → `append_to_log()` → `invalidate_index_cache()` → `cache_store.invalidate_all()`

## Data Contracts

### AnalyzeRequest → AnalyzeResponse
- **Input**: `content: str`, `filename?: str`
- **Output**: `success: bool`, `suggested_pages: [SuggestedPageModel]`, `confidence: float`, `raw_text_preview: str`

### FileIngestResponse
- `pages_created: [str]`, `pages_updated: [str]`, `total_pages: int`, `nodes_created: int`, `relationships_created: int`

### FolderIngestResponse
- `total_files: int`, `total_pages_created: int`, `total_pages_updated: int`, `file_results: [FileIngestResponse]`

## See Also

- [[wiki-file-system]]
- [[chat-to-wiki-pipeline]]
- [[knowledge-graph-ingestion]]
- [[api-design]]
- [[agent-architecture]]

