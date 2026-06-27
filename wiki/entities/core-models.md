---
title: "Core Models"
tags: [models, pydantic, schema]
created: 2026-06-22
updated: 2026-06-26
sources: [pydantic-2026]
related: [pydantic-ai, pydantic-graph, knowledge-graph-schema, api-design]
---

# Core Models

All request/response models in `src/models.py` (216 lines), typed with Pydantic v2. They form the shared contract between the API, agents, and SwiftUI client.

## Request Models

| Model | Key Fields | Used By |
|-------|-----------|---------|
| `QueryRequest` | `query: str`, `structured: bool`, `conversation_id?: str` | `POST /query`, `POST /consensus/query` |
| `NavigateRequest` | `origin: str`, `destination: str`, `target_year: int`, `energy_level: float` | `POST /navigate` |
| `IngestRequest` | `title: str`, `content: str`, `tags: List[str]`, `sources: List[str]` | `POST /ingest` (Celery sync) |
| `AnalyzeRequest` | `content: str`, `filename?: str` | `POST /ingest/analyze` |
| `LLMConfigRequest` | `llm_active_provider?: str`, `llm_active_model?: str` | `POST /config/llm` |
| `LLMProbeRequest` | `provider_name: str` (omlx/ollama/lmstudio) | `POST /config/llm/probe` |
| `ConfigRequest` | `quantum_backend: str`, `*api_token?: str`, `quantum_hardware_enabled: bool`, `llm_active_provider?: str`, `llm_active_model?: str` | `POST /config` |
| `SetUserNameRequest` | `name: str` (1-100 chars) | `POST /chat/name` |

## Response Models

| Model | Key Fields | Used By |
|-------|-----------|---------|
| `QueryResponse` | `query`, `answer`, `confidence`, `entities[]`, `sources[]`, `inferred_events[]`, `inferred_entities[]`, `conversation_id?`, `history[]` | `POST /query` |
| `NavigateResponse` | `success`, `path[]`, `warp_factor`, `divergence_risk`, `geometry_tensor` | `POST /navigate` |
| `IngestResponse` | `success`, `nodes_created`, `relationships_created`, `confidence_score` | `POST /ingest` |
| `AnalyzeResponse` | `success`, `suggested_pages[]`, `confidence`, `raw_text_preview` | `POST /ingest/analyze` |
| `SuggestedPageModel` | `title`, `page_type` (entities/concepts/projects), `tags[]`, `sources[]`, `summary`, `body`, `related[]`, `confidence` | Used in `AnalyzeResponse` |
| `FileIngestResponse` | `success`, `pages_created[]`, `pages_updated[]`, `total_pages`, `nodes_created`, `relationships_created` | `POST /ingest/file` |
| `FolderIngestResponse` | `success`, `total_files`, `total_pages_created/updated`, `total_nodes/relationships_created`, `file_results[]`, `failed_files[]` | `POST /ingest/folder` |
| `StatusResponse` | `status`, `llm_provider`, `llm_connected`, `neo4j_connected`, `redis_connected`, `quantum_backend` | `GET /status` |
| `ModelsResponse` | `provider`, `models[]` | `GET /models` |
| `ConfigResponse` | `success`, `quantum_backend`, `quantum_hardware_enabled`, `*api_token_set`, `llm_active_provider/model`, `llm_available_models[]`, `llm_providers: Dict[LLMProviderStatus]` | `GET /config` |
| `LLMConfigResponse` | `success`, `llm_active_provider/model`, `llm_available_models[]`, `llm_providers` | `POST /config/llm` |
| `LLMProbeResponse` | `provider`, `available`, `models[]` | `POST /config/llm/probe` |
| `LLMProviderStatus` | `available: bool`, `models: List[str]` | Embedded in `ConfigResponse` |
| `ConversationMetaResponse` | `id`, `message_count`, `last_activity?`, `ingested`, `ingested_at?`, `pages_created[]` | `GET /conversations` |
| `ChatIngestStatusResponse` | `enabled`, `last_run?`, `conversations_checked/ingested`, `pages_created/updated` | `GET /chat/ingest/status` |
| `SetUserNameResponse` | `success`, `previous_name`, `current_name`, `slug` | `POST /chat/name` |

## Wiki Models

| Model | Key Fields | Used By |
|-------|-----------|---------|
| `WikiPageListItem` | `slug`, `title`, `page_type`, `tags[]`, `created`, `updated`, `protected` | `GET /wiki/pages` |
| `WikiPageListResponse` | `success`, `pages[]`, `total` | `GET /wiki/pages` |
| `WikiPageDetailResponse` | `success`, `slug`, `title`, `page_type`, `tags[]`, `sources[]`, `related[]`, `body`, `created`, `updated`, `protected` | `GET /wiki/page/{slug}` |
| `WikiDeleteResponse` | `success`, `slug`, `page_type`, `title`, `neo4j_cleaned`, `cross_refs_cleaned` | `DELETE /wiki/page/{slug}` |
| `WikiClearResponse` | `success`, `dry_run`, `preserved/deleted/protected_added_count`, `preserved_slugs[]`, `deleted_slugs[]` | `POST /wiki/clear` |
| `WikiExportResponse` | `success`, `filepath`, `size_kb`, `page_count` | `POST /wiki/export` |
| `WikiImportResponse` | `success`, `restored_count` | `POST /wiki/import` |

## SwiftUI Equivalents

The SwiftUI client mirrors these models in `APIModels.swift` (822 lines) as `Codable` structs. Each Pydantic model has a corresponding Swift struct with matching field names and types. Key mappings:

| Python | Swift |
|--------|-------|
| `QueryRequest` | `APIQueryRequest` |
| `QueryResponse` | `APIQueryResponse` |
| `NavigateRequest/Response` | `APINavigateRequest` / `APINavigateResponse` |
| `FileIngestResponse` | `APIFileIngestResponse` |
| `FolderIngestResponse` | `APIFolderIngestResponse` |
| `ChatIngestStatusResponse` | `APIChatIngestStatus` |
| `SetUserNameRequest/Response` | `APISetUserNameRequest` / `APISetUserNameResponse` |
| `ConversationMetaResponse` | `APIConversationMeta` |

## See Also

- [[api-design]] — All API endpoints using these models
- [[pydantic-ai]] — Pydantic AI framework
- [[pydantic-graph]] — Pydantic Graph for agent orchestration
- [[swift-frontend-architecture]] — SwiftUI Codable equivalents
