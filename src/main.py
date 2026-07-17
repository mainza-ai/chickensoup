import json
import re
import logging
import os
import io
import zipfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
import json
import time
import redis

from src.tasks import task_registry, TaskStatusModel
from src.models import AsyncTaskResponse
from src.api.auth import verify_api_key

from src.config import settings
from src.discovery import discover_active_provider, get_discovered, get_active_model, get_active_provider, refresh_discovery, probe_provider, get_all_providers
from typing import Any, Dict, List, Optional
from src.models import (
    QueryRequest, QueryResponse, NavigateRequest, NavigateResponse,
    SimulateRequest, SimulateResponse,
    IngestRequest, IngestResponse, StatusResponse, ModelsResponse,
    ConfigRequest, ConfigResponse, LLMConfigRequest, LLMConfigResponse,
    LLMProbeRequest, LLMProbeResponse, LLMProviderStatus,
    AnalyzeRequest, AnalyzeResponse, SuggestedPageModel,
    FileIngestResponse, FolderIngestResponse,
    PdfFolderIngestRequest, PdfFolderIngestResponse,
    ConversationMetaResponse, ChatIngestStatusResponse,
    SetUserNameRequest, SetUserNameResponse,
    WikiClearResponse, WikiExportResponse, WikiImportResponse,
    WikiPageListItem, WikiPageListResponse, WikiPageDetailResponse, WikiDeleteResponse,
    PulseResult, DivergenceResult, ClaimConfidence, TimelinePoint, BudgetStatus,
    ClaimEvidence,
)
from src.knowledge_graph.connection import neo4j_conn
from src.knowledge_graph.schema import initialize_schema
from src.knowledge_graph.ingest import ingest_wiki_page
from src.knowledge_graph.queries import get_entity_neighborhood, search_entities, fulltext_search
from src.knowledge_graph.temporal import get_temporal_events, get_entity_temporal_context, get_timeline_range
from src.spacetime_engine.qiskit_simulation import simulate_spacetime_metrics
from src.field_manipulator.cuda_simulation import manipulate_spacetime_field
from src.ai_navigator.pennylane_qml import find_optimal_path
from src.agents.orchestrator import Orchestrator
from src.agents.ingest_agent import IngestAgent
from src.wiki.writer import write_page, append_to_index, append_to_log, slugify, cross_reference_new_page, invalidate_index_cache, delete_page, read_page
from src.mcp.tools import mcp

ingest_agent = IngestAgent()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chickensoup.main")

# Initialize agent orchestrator
orchestrator = Orchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up chickensoup API...")
    scheduler_task = None
    almanac_task = None
    watcher_task = None
    daily_rebuild_task = None
    try:
        driver = neo4j_conn.connect()
        initialize_schema(driver)
    except Exception as e:
        logger.error(f"Could not initialize Neo4j connection or schema on startup: {e}")

    # Auto-restore Neo4j from seed dump if database is empty
    if settings.NEO4J_BACKUP_ENABLED:
        try:
            from pathlib import Path
            seed_path = Path(settings.NEO4J_BACKUP_DIR) / "seed.dump"
            if seed_path.exists():
                from src.neo4j_backup import needs_restore, restore_backup
                if needs_restore(driver):
                    logger.info("Neo4j database is empty — restoring from seed dump...")
                    success = restore_backup("seed.dump")
                    if success:
                        logger.info("Neo4j restored from seed dump successfully")
                        driver = neo4j_conn.connect()
                        initialize_schema(driver)
                    else:
                        logger.warning("Neo4j seed restore failed — starting fresh")
        except Exception as e:
            logger.warning(f"Could not check/restore Neo4j seed: {e}")

    try:
        from src.scheduler import periodic_chat_ingest_loop
        scheduler_task = asyncio.create_task(periodic_chat_ingest_loop())
        logger.info("Chat-to-wiki scheduler started")
    except Exception as e:
        logger.warning(f"Could not start chat-to-wiki scheduler: {e}")

    try:
        from src.scheduler import idle_ingestion_loop
        almanac_task = asyncio.create_task(idle_ingestion_loop())
        logger.info("Idle-driven ingestion loop started")
    except Exception as e:
        logger.warning(f"Could not start idle-driven ingestion loop: {e}")

    try:
        from src.wiki.watcher import wiki_watcher_loop
        watcher_task = asyncio.create_task(wiki_watcher_loop())
        logger.info("Wiki filesystem watcher started")
    except Exception as e:
        logger.warning(f"Could not start wiki watcher: {e}")

    try:
        from src.scheduler import rebuild_queue_daily_loop
        daily_rebuild_task = asyncio.create_task(rebuild_queue_daily_loop())
        logger.info("Daily queue rebuild loop started")
    except Exception as e:
        logger.warning(f"Could not start daily queue rebuild loop: {e}")

    try:
        from src.scheduler import fallback_retry_loop
        asyncio.create_task(fallback_retry_loop())
        logger.info("Fallback retry loop started")
    except Exception as e:
        logger.warning(f"Could not start fallback retry loop: {e}")

    # Deferred reconciliation: process any pages that exist on disk but haven't
    # been ingested (e.g. restored from git while server was down). Runs in a
    # thread executor to avoid blocking the event loop during O(n) cross-ref scan.
    # Skipped in test environments to avoid background threads interfering with
    # mock state and causing test hangs.
    if settings.WIKI_RECONCILE_ON_STARTUP and not os.environ.get("PYTEST_VERSION"):
        try:
            from src.reconciliation_gate import clear_stale_gate
            clear_stale_gate()
        except Exception:
            pass
        try:
            from src.idle_sentinel import IdleSentinel
            IdleSentinel.clear_stale_keys()
        except Exception:
            pass
        try:
            from src.wiki.watcher import reconcile_existing_pages
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, reconcile_existing_pages)
            logger.info("Wiki reconciliation dispatched to thread executor")
        except Exception as e:
            logger.warning(f"Could not start wiki reconciliation: {e}")

    # Sync the staleness queue with the filesystem at startup
    try:
        from src.staleness_queue import rebuild_queue
        rebuild_queue()
        logger.info("Staleness queue rebuilt at startup")
    except Exception as e:
        logger.warning(f"Could not rebuild staleness queue at startup: {e}")

    # Reset LLM client metrics at startup so stale failure counts don't persist
    try:
        from src.progress_tracker import update as progress_update
        progress_update("llm_client", total_calls="0", success_calls="0", failed_calls="0", breaker_open="false")
        logger.info("LLM client progress counters reset at startup")
    except Exception as e:
        logger.warning(f"Could not reset LLM client progress counters: {e}")

    # Build temporal causality chains between dated Event nodes
    try:
        from src.knowledge_graph.temporal_causality import build_temporal_causality_chains
        driver = neo4j_conn.get_driver()
        if driver:
            result = build_temporal_causality_chains(driver)
            if result["events_processed"] > 0:
                logger.info(f"Temporal causality chains built: {result['preceded_by']} preceded_by, {result['caused']} caused")
    except Exception as e:
        logger.warning(f"Could not build temporal causality chains: {e}")

    # Start Neo4j backup scheduler if enabled
    neo4j_backup_task = None
    if settings.NEO4J_BACKUP_ENABLED:
        try:
            from src.scheduler import neo4j_backup_loop
            neo4j_backup_task = asyncio.create_task(neo4j_backup_loop())
            logger.info("Neo4j backup scheduler started")
        except Exception as e:
            logger.warning(f"Could not start Neo4j backup scheduler: {e}")

    # Start automatic almanac generation loop
    almanac_gen_task = None
    try:
        from src.scheduler import almanac_generation_loop
        almanac_gen_task = asyncio.create_task(almanac_generation_loop())
        logger.info(f"Almanac generation scheduler started ({settings.ALMANAC_GENERATION_INTERVAL_HOURS}h interval)")
    except Exception as e:
        logger.warning(f"Could not start almanac generation scheduler: {e}")

    yield
    logger.info("Shutting down chickensoup API...")
    for task in (scheduler_task, almanac_task, watcher_task, daily_rebuild_task, neo4j_backup_task, almanac_gen_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    neo4j_conn.close()

def _build_llm_providers() -> Dict[str, LLMProviderStatus]:
    """Build the llm_providers dict from the full discovery cache."""
    from src.discovery import get_all_providers
    raw = get_all_providers()
    return {
        name: LLMProviderStatus(
            available=info.get("available", False),
            models=info.get("models", []),
        )
        for name, info in raw.items()
    }

_VALID_ENTITY_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9 _\-\.]{1,100}$')

def _validate_entity_name(name: str, field: str = "entity_name") -> str:
    """Validate and normalize an entity name from a path parameter.
    
    Rejects punctuation-only names, empty strings, and names with
    suspicious characters. Returns the stripped name if valid.
    """
    if not name or not name.strip():
        raise HTTPException(status_code=422, detail=f"{field} must not be empty.")
    stripped = name.strip()
    if not _VALID_ENTITY_NAME_RE.match(stripped):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field}: '{stripped}'. Must start with alphanumeric, contain only alphanumerics, spaces, hyphens, underscores, and dots, and be 2-100 characters.",
        )
    return stripped

def _update_env_file(updates: dict):
    """Persist key-value pairs to .env, preserving existing lines."""
    try:
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()

        updated_keys = set()
        new_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                new_lines.append(line)
                continue
            parts = line_str.split("=", 1)
            key = parts[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)

        for key, val in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={val}\n")

        with open(env_path, "w") as f:
            f.writelines(new_lines)
    except Exception as e:
        logger.error(f"Failed to update .env: {e}")

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
from src.observability import tracer, agent_loop_counter, quantum_simulation_duration
from src.cache import cache_store, cache_decorator

# CORS origins — configurable via CORS_ORIGINS env var
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app = FastAPI(
    title="Project Chicken Soup API",
    description="FastAPI & FastMCP spacetime simulation & UAP lore navigation backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenTelemetry tracking + Rate Limiting Middleware
class ObservabilityAndRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        with tracer.start_as_current_span(f"http_request_{request.method}_{request.url.path}"):
            response = await call_next(request)
            return response

app.add_middleware(ObservabilityAndRateLimitMiddleware)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with body larger than settings.REQUEST_MAX_BODY_BYTES."""

    def __init__(self, app, max_size: int = None):
        super().__init__(app)
        self.max_size = max_size or settings.REQUEST_MAX_BODY_BYTES

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return Response(
                content=json.dumps({"detail": f"Payload too large. Max size is {self.max_size} bytes."}),
                media_type="application/json",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        return await call_next(request)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign a unique X-Request-ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        import uuid
        request_id = request.headers.get(settings.REQUEST_ID_HEADER) or str(uuid.uuid4())
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        response = await call_next(request)
        response.headers[settings.REQUEST_ID_HEADER] = request_id
        return response


class ConcurrencySemaphoreMiddleware(BaseHTTPMiddleware):
    """Deprecated: LLM concurrency is now managed by LLMClient's priority
    semaphore system (2 high + 2 low). This middleware is kept as a passthrough
    for backward compatibility but does no gating."""

    async def dispatch(self, request: Request, call_next) -> Response:
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RequestIdMiddleware)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP and per-API-key rate limiting using sliding window with differentiated categories."""

    ROUTE_CATEGORIES: dict[str, str] = {
        "search": "search",
        "graph": "search",
        "entities": "read",
        "events": "read",
        "timeline": "read",
        "wiki/pages": "read",
        "wiki/page": "read",
        "status": "read",
        "health": "read",
        "config": "read",
        "models": "read",
        "conversation": "read",
        "ingest": "write",
        "wiki/clear": "write",
        "wiki/export": "write",
        "wiki/import": "write",
        "research": "write",
        "simulate": "search",
    }

    def __init__(self, app):
        super().__init__(app)
        from src.rate_limiter import rate_limiter
        self._limiter = rate_limiter

    def _get_category(self, path: str) -> str:
        for prefix, category in self.ROUTE_CATEGORIES.items():
            if path.startswith(f"/{prefix}"):
                return category
        return "general"

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.RATE_LIMITING_ENABLED:
            return await call_next(request)

        if request.url.path in ("/health", "/status", "/status/progress", "/status/time"):
            return await call_next(request)

        category = self._get_category(request.url.path)

        client_ip = request.client.host if request.client else "unknown"
        ip_allowed, ip_remaining = self._limiter.check_ip(client_ip, category)
        if not ip_allowed:
            return Response(
                content=json.dumps({"detail": f"Rate limit exceeded for {category}. Try again in 60s.", "retry_after": 60}),
                media_type="application/json",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": "60"},
            )

        api_key = request.headers.get("X-Api-Key", "")
        if api_key:
            key_allowed, key_remaining = self._limiter.check_api_key(api_key, category)
            if not key_allowed:
                return Response(
                    content=json.dumps({"detail": f"API key rate limit exceeded for {category}. Try again in 10s.", "retry_after": 10}),
                    media_type="application/json",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": "10"},
                )

        response = await call_next(request)
        return response


app.add_middleware(RateLimitMiddleware)


@app.get("/health")
async def health_check():
    """Deep health probe with per-component latency and status."""
    import time as _time
    checks = {}
    
    # Redis
    redis_start = _time.time()
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = {"ok": True, "latency_ms": round((_time.time() - redis_start) * 1000)}
    except Exception as e:
        checks["redis"] = {"ok": False, "latency_ms": None, "error": str(e)}
    
    # Neo4j
    neo4j_start = _time.time()
    try:
        neo4j_ok = neo4j_conn.check_health()
        checks["neo4j"] = {"ok": neo4j_ok, "latency_ms": round((_time.time() - neo4j_start) * 1000)}
    except Exception as e:
        checks["neo4j"] = {"ok": False, "latency_ms": None, "error": str(e)}
    
    # LLM
    llm_start = _time.time()
    try:
        provider, _, _ = get_discovered(depth="fresh")
        llm_ok = provider != "simulated"
        checks["llm"] = {"ok": llm_ok, "latency_ms": round((_time.time() - llm_start) * 1000), "provider": provider}
    except Exception as e:
        checks["llm"] = {"ok": False, "latency_ms": None, "error": str(e)}
    
    # Disk
    disk_start = _time.time()
    try:
        import shutil
        free_gb = shutil.disk_usage(".").free / (1024 ** 3)
        checks["disk"] = {"ok": free_gb > 1.0, "free_gb": round(free_gb, 1), "latency_ms": round((_time.time() - disk_start) * 1000)}
    except Exception as e:
        checks["disk"] = {"ok": False, "error": str(e)}
    
    all_ok = all(c.get("ok") for c in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "checks": checks}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Returns system status, showing connectivity of local LLMs, database, and cache."""
    provider, _, _ = get_discovered(depth="fresh")
    llm_connected = provider != "simulated"

    neo4j_ok = neo4j_conn.check_health()

    redis_ok = False
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    last30days_enabled = settings.LAST30DAYS_ENABLED
    budget_remaining = None
    try:
        if last30days_enabled:
            from src.budget import budget_tracker
            bs = budget_tracker.get_status()
            budget_remaining = bs.remaining_usd
    except Exception:
        pass

    return StatusResponse(
        status="healthy" if (neo4j_ok or llm_connected) else "degraded",
        llm_provider=provider,
        llm_connected=llm_connected,
        neo4j_connected=neo4j_ok,
        redis_connected=redis_ok,
        quantum_backend=settings.QUANTUM_SIMULATION_BACKEND,
        last30days_enabled=last30days_enabled,
        budget_remaining=budget_remaining,
    )

@app.get("/tasks/{task_id}", response_model=TaskStatusModel)
async def get_task_status(task_id: str):
    """Retrieves status, progress, and logs for a background task."""
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID '{task_id}' not found")
    return task.to_model()

@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Returns current quantum and LLM settings (always probes fresh)."""
    provider, _, models = get_discovered(depth="fresh")
    all_providers_raw = get_all_providers()
    llm_providers = {}
    for name, info in all_providers_raw.items():
        llm_providers[name] = LLMProviderStatus(
            available=info.get("available", False),
            models=info.get("models", []),
            type=info.get("type", "local"),
            api_key_configured=bool(info.get("api_key")),
        )
    return ConfigResponse(
        success=True,
        quantum_backend=settings.QUANTUM_SIMULATION_BACKEND,
        quantum_hardware_enabled=settings.QUANTUM_HARDWARE_ENABLED,
        ibm_api_token_set=bool(settings.IBM_API_TOKEN),
        dwave_api_token_set=bool(settings.DWAVE_API_TOKEN),
        ionq_api_token_set=bool(settings.IONQ_API_TOKEN),
        llm_active_provider=get_active_provider(),
        llm_active_model=get_active_model(),
        llm_available_models=models,
        llm_providers=llm_providers,
        llm_provider_type=settings.LLM_PROVIDER_TYPE,
        nvidia_api_key_set=bool(settings.NVIDIA_API_KEY),
        openrouter_api_key_set=bool(settings.OPENROUTER_API_KEY),
        custom_llm_api_url_set=bool(settings.CUSTOM_LLM_API_URL),
        last30days_enabled=settings.LAST30DAYS_ENABLED,
    )

@app.post("/config", response_model=ConfigResponse, dependencies=[Depends(verify_api_key)])
async def post_config(request: ConfigRequest):
    """Updates quantum and/or LLM settings and persists to .env."""
    settings.QUANTUM_SIMULATION_BACKEND = request.quantum_backend
    settings.QUANTUM_HARDWARE_ENABLED = request.quantum_hardware_enabled
    if request.ibm_api_token is not None:
        settings.IBM_API_TOKEN = request.ibm_api_token
    if request.dwave_api_token is not None:
        settings.DWAVE_API_TOKEN = request.dwave_api_token
    if request.ionq_api_token is not None:
        settings.IONQ_API_TOKEN = request.ionq_api_token

    if request.llm_active_provider is not None:
        settings.LLM_ACTIVE_PROVIDER = request.llm_active_provider
    if request.llm_active_model is not None:
        settings.LLM_ACTIVE_MODEL = request.llm_active_model
    if request.llm_provider_type is not None:
        settings.LLM_PROVIDER_TYPE = request.llm_provider_type
    if request.nvidia_api_key is not None:
        settings.NVIDIA_API_KEY = request.nvidia_api_key
    if request.openrouter_api_key is not None:
        settings.OPENROUTER_API_KEY = request.openrouter_api_key
    if request.custom_llm_api_key is not None:
        settings.CUSTOM_LLM_API_KEY = request.custom_llm_api_key
    if request.custom_llm_api_url is not None:
        settings.CUSTOM_LLM_API_URL = request.custom_llm_api_url
    if request.custom_llm_models is not None:
        settings.CUSTOM_LLM_MODELS = request.custom_llm_models

    # Refresh discovery with new config
    provider, _, models = refresh_discovery()

    updates = {
        "QUANTUM_SIMULATION_BACKEND": settings.QUANTUM_SIMULATION_BACKEND,
        "QUANTUM_HARDWARE_ENABLED": str(settings.QUANTUM_HARDWARE_ENABLED).lower(),
        "LLM_ACTIVE_PROVIDER": settings.LLM_ACTIVE_PROVIDER,
        "LLM_ACTIVE_MODEL": settings.LLM_ACTIVE_MODEL,
        "LLM_PROVIDER_TYPE": settings.LLM_PROVIDER_TYPE,
    }
    if request.ibm_api_token is not None:
        updates["IBM_API_TOKEN"] = settings.IBM_API_TOKEN
    if request.dwave_api_token is not None:
        updates["DWAVE_API_TOKEN"] = settings.DWAVE_API_TOKEN
    if request.ionq_api_token is not None:
        updates["IONQ_API_TOKEN"] = settings.IONQ_API_TOKEN
    if request.nvidia_api_key is not None:
        updates["NVIDIA_API_KEY"] = settings.NVIDIA_API_KEY
    if request.openrouter_api_key is not None:
        updates["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    if request.custom_llm_api_key is not None:
        updates["CUSTOM_LLM_API_KEY"] = settings.CUSTOM_LLM_API_KEY
    if request.custom_llm_api_url is not None:
        updates["CUSTOM_LLM_API_URL"] = settings.CUSTOM_LLM_API_URL
    if request.custom_llm_models is not None:
        updates["CUSTOM_LLM_MODELS"] = settings.CUSTOM_LLM_MODELS

    _update_env_file(updates)

    all_providers_raw = get_all_providers()
    llm_providers = {}
    for name, info in all_providers_raw.items():
        llm_providers[name] = LLMProviderStatus(
            available=info.get("available", False),
            models=info.get("models", []),
            type=info.get("type", "local"),
            api_key_configured=bool(info.get("api_key")),
        )
    return ConfigResponse(
        success=True,
        quantum_backend=settings.QUANTUM_SIMULATION_BACKEND,
        quantum_hardware_enabled=settings.QUANTUM_HARDWARE_ENABLED,
        ibm_api_token_set=bool(settings.IBM_API_TOKEN),
        dwave_api_token_set=bool(settings.DWAVE_API_TOKEN),
        ionq_api_token_set=bool(settings.IONQ_API_TOKEN),
        llm_active_provider=get_active_provider(),
        llm_active_model=get_active_model(),
        llm_available_models=models,
        llm_providers=llm_providers,
        llm_provider_type=settings.LLM_PROVIDER_TYPE,
        nvidia_api_key_set=bool(settings.NVIDIA_API_KEY),
        openrouter_api_key_set=bool(settings.OPENROUTER_API_KEY),
        custom_llm_api_url_set=bool(settings.CUSTOM_LLM_API_URL),
        last30days_enabled=settings.LAST30DAYS_ENABLED,
    )

@app.post("/config/llm", response_model=LLMConfigResponse, dependencies=[Depends(verify_api_key)])
async def post_llm_config(request: LLMConfigRequest):
    """Updates LLM provider/model selection, forces fresh probe, persists to .env."""
    if request.llm_active_provider is not None:
        settings.LLM_ACTIVE_PROVIDER = request.llm_active_provider
    if request.llm_active_model is not None:
        settings.LLM_ACTIVE_MODEL = request.llm_active_model

    # Invalidate cached LLM responses so they re-fetch with new provider/model
    cache_store.invalidate_by_pattern("cache:llm:*")
    cache_store.invalidate_by_pattern("cache:mcp:*")

    provider, _, models = refresh_discovery()

    _update_env_file({
        "LLM_ACTIVE_PROVIDER": settings.LLM_ACTIVE_PROVIDER,
        "LLM_ACTIVE_MODEL": settings.LLM_ACTIVE_MODEL,
    })

    return LLMConfigResponse(
        success=True,
        llm_active_provider=get_active_provider(),
        llm_active_model=get_active_model(),
        llm_available_models=models,
        llm_providers=_build_llm_providers(),
    )

@app.post("/config/llm/probe", response_model=LLMProbeResponse)
async def post_llm_probe(request: LLMProbeRequest):
    """Probe a specific provider and return its models (does not change active config)."""
    provider, _, models = probe_provider(request.provider_name)
    return LLMProbeResponse(
        provider=provider,
        available=provider != "simulated",
        models=models,
    )

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Lists available local LLM models discovered on the system fallback chain."""
    provider, _, models = get_discovered(depth="fresh")
    return ModelsResponse(
        provider=provider,
        models=models
    )

def _build_query_response(query: str, output: Dict[str, Any], conversation_id: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> QueryResponse:
    answer = output.get("answer", "No response generated.")
    if output.get("status") == "paused_for_human_approval":
        answer = f"PENDING APPROVAL: {output.get('summary', '')}"

    # Claim confidences from wavefunction scoring — now actually populated
    claim_confs = []
    try:
        wf_scores = output.get("wavefunction_scores", {}) or output.get("research_details", {}).get("wavefunction_scores", {})
        if wf_scores:
            for name, detail in wf_scores.items():
                if isinstance(detail, dict):
                    try:
                        from src.models import ClaimConfidence
                        claim_confs.append(ClaimConfidence(**{
                            k: v for k, v in detail.items()
                            if k in ClaimConfidence.model_fields
                        }))
                    except Exception:
                        continue
    except Exception:
        pass

    inferred_events = output.get("inferred_events", []) or output.get("research_details", {}).get("inferred_events", [])
    inferred_entities = output.get("inferred_entities", []) or output.get("research_details", {}).get("inferred_entities", [])

    source_tier = "network_opt_in" if claim_confs else "local"

    query_status = output.get("status", "completed")

    return QueryResponse(
        query=query,
        answer=answer,
        confidence=output.get("confidence", 0.5),
        entities=output.get("entities", []),
        sources=output.get("sources", ["Orchestrated Search"]) if not query_status == "paused_for_human_approval" else [],
        inferred_events=inferred_events,
        inferred_entities=inferred_entities,
        conversation_id=conversation_id,
        history=history or [],
        claim_confidences=claim_confs,
        source_tier=source_tier,
        task_id=output.get("task_id"),
        thread_id=output.get("thread_id"),
        status=query_status,
    )


def _conversation_redis_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}"


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history by ID."""
    try:
        from src.cache import cache_store, cache_decorator
        raw = cache_store.get(_conversation_redis_key(conversation_id))
        if raw:
            return {"conversation_id": conversation_id, "history": json.loads(raw)}
    except Exception as e:
        logger.warning(f"Failed to retrieve conversation {conversation_id}: {e}")
    return {"conversation_id": conversation_id, "history": []}


@app.get("/conversations")
async def list_conversations():
    """List all conversations with metadata."""
    try:
        from src.scheduler import get_all_conversation_ids, get_conversation_meta
        ids = get_all_conversation_ids()
        results = []
        for cid in ids:
            meta = get_conversation_meta(cid)
            results.append(ConversationMetaResponse(
                id=cid,
                message_count=meta.get("message_count", 0),
                last_activity=meta.get("last_activity"),
                ingested=meta.get("ingested", False),
                ingested_at=meta.get("ingested_at"),
                pages_created=meta.get("pages_created", []),
            ))
        return {"conversations": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        return {"conversations": [], "total": 0}


@app.get("/chat/ingest/status", response_model=ChatIngestStatusResponse)
async def get_chat_ingest_status():
    """Returns the status of the periodic chat-to-wiki converter."""
    from src.scheduler import get_status
    return ChatIngestStatusResponse(**get_status())


@app.post("/chat/ingest/now", dependencies=[Depends(verify_api_key)])
async def trigger_chat_ingest():
    """Manually triggers an immediate chat-to-wiki scan."""
    try:
        from src.scheduler import process_eligible_conversations
        await process_eligible_conversations()
        from src.scheduler import get_status
        return {"success": True, "status": get_status()}
    except Exception as e:
        logger.error(f"Manual chat ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/ingest/history")
async def get_chat_ingest_history(limit: int = 20):
    """Returns detailed ingest history with per-entity breakdown."""
    from src.scheduler import get_ingest_history
    return {"history": get_ingest_history(limit=limit)}


@app.get("/chat/ingest/notifications")
async def get_chat_ingest_notifications(limit: int = 10):
    """Returns recent chat-ingest notifications for the frontend."""
    from src.scheduler import get_recent_notifications
    return {"notifications": get_recent_notifications(limit=limit)}


@app.post("/chat/name", response_model=SetUserNameResponse)
async def set_user_name(request: SetUserNameRequest):
    """Set or update the user's wiki entity name."""
    from src.wiki.writer import read_page, write_page, slugify, delete_page

    current_name = settings.CHAT_WIKI_USER_ENTITY_NAME
    current_slug = slugify(current_name)
    new_slug = slugify(request.name)

    existing = read_page(current_slug, page_type="entities")
    if not existing:
        settings.CHAT_WIKI_USER_ENTITY_NAME = request.name
        return SetUserNameResponse(
            success=True,
            previous_name=current_name,
            current_name=request.name,
            slug=new_slug,
        )

    frontmatter = existing["frontmatter"]
    write_page(
        title=request.name,
        body=existing["body"],
        tags=frontmatter.get("tags", ["person", "user"]),
        sources=frontmatter.get("sources", []),
        related=frontmatter.get("related", []),
        page_type="entities",
    )

    if new_slug != current_slug:
        try:
            delete_page(current_slug, page_type="entities")
        except Exception as e:
            logger.warning(f"Failed to delete old user entity page '{current_slug}': {e}")

    settings.CHAT_WIKI_USER_ENTITY_NAME = request.name
    return SetUserNameResponse(
        success=True,
        previous_name=current_name,
        current_name=request.name,
        slug=new_slug,
    )


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
async def post_query(request: QueryRequest):
    """Submits a query to search the knowledge graph and generate an answer summary using Orchestrator."""
    try:
        if len(request.query.encode("utf-8")) > 102_400:
            raise HTTPException(status_code=413, detail="Query exceeds 100KB limit")
        import uuid
        from src.idle_sentinel import IdleSentinel
        IdleSentinel.update_activity("query")

        conversation_id = request.conversation_id or str(uuid.uuid4())
        history: List[Dict[str, str]] = []

        # Retrieve prior conversation turns from Redis
        try:
            from src.cache import cache_store, cache_decorator
            raw = cache_store.get(_conversation_redis_key(conversation_id))
            if raw:
                history = json.loads(raw)
        except Exception as e:
            logger.warning(f"Failed to retrieve conversation history: {e}")

        output = await orchestrator.execute(request.query, history=history)
        response = _build_query_response(request.query, output, conversation_id=conversation_id, history=history)

        # Async enrichment: return immediately with task_id instead of blocking answer
        if output.get("status") == "task_created":
            return response

        # Store updated conversation
        history.append({"role": "user", "content": request.query})
        history.append({"role": "assistant", "content": response.answer})
        try:
            from src.cache import cache_store, cache_decorator
            cache_store.set(_conversation_redis_key(conversation_id), json.dumps(history[-20:]), ttl=604800)

            # Update conversation meta for chat-to-wiki scheduler
            from datetime import datetime, timezone
            from src.scheduler import update_conversation_meta, add_eligible_conversation
            meta_key = f"conversation:{conversation_id}:meta"
            existing_meta = cache_store.get(meta_key) or {}
            message_count = existing_meta.get("message_count", 0) + 1
            existing_meta["message_count"] = message_count
            existing_meta["last_activity"] = datetime.now(timezone.utc).isoformat()
            if "ingested" not in existing_meta:
                existing_meta["ingested"] = False
            cache_store.set(meta_key, existing_meta, ttl=604800)

            if message_count >= settings.CHAT_WIKI_MIN_CONVERSATION_LENGTH:
                add_eligible_conversation(conversation_id)
        except Exception as e:
            logger.warning(f"Failed to store conversation or update meta: {e}")

        return response
    except Exception as e:
        logger.error(f"Error handling orchestrated query: {e}")
        return QueryResponse(
            query=request.query,
            answer=f"Error processing query: {str(e)}",
            confidence=0.0,
            entities=[],
            sources=[],
            inferred_events=[],
            inferred_entities=[],
            conversation_id=request.conversation_id,
        )

@app.get("/graph/{entity}")
async def get_graph_entity(entity: str):
    entity = _validate_entity_name(entity, "entity")
    """Retrieves an entity and all its directly related nodes/relationships in a simplified form."""
    import uuid
    try:
        driver = neo4j_conn.get_driver()
        details = get_entity_neighborhood(driver, entity)
        if not details.get("entity"):
            raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found.")
        
        entity_info = details["entity"]
        labels = entity_info["labels"]
        entity_type = "Entity"
        for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
            if label in labels:
                entity_type = label
                break
                
        props = entity_info["properties"]
        sources = props.get("sources", [])
        if not isinstance(sources, list):
            sources = [str(sources)] if sources else []
            
        simple_entity = {
            "id": entity_info["name"].lower(),
            "name": entity_info["name"],
            "type": entity_type,
            "summary": props.get("content_preview", props.get("summary", "")),
            "confidence": props.get("confidence", 1.0),
            "source": sources[0] if sources else "Unknown",
            "sources": [str(s) for s in sources]
        }
        
        simple_connections = []
        for conn in details["connections"]:
            n_labels = conn["neighbor_labels"]
            n_type = "Entity"
            for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
                if label in n_labels:
                    n_type = label
                    break
            
            n_props = conn["neighbor_properties"]
            n_sources = n_props.get("sources", [])
            if not isinstance(n_sources, list):
                n_sources = [str(n_sources)] if n_sources else []
                
            simple_connections.append({
                "relationship_type": conn["relationship_type"],
                "neighbor": {
                    "id": conn["neighbor_name"].lower(),
                    "name": conn["neighbor_name"],
                    "type": n_type,
                    "summary": n_props.get("content_preview", n_props.get("summary", "")),
                    "confidence": n_props.get("confidence", 1.0),
                    "source": n_sources[0] if n_sources else "Unknown",
                    "sources": [str(s) for s in n_sources]
                }
            })
            
        return {
            "entity": simple_entity,
            "connections": simple_connections
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/navigate", response_model=NavigateResponse, dependencies=[Depends(verify_api_key)])
async def post_navigate(request: NavigateRequest):
    """Computes the optimal path through the warped spacetime manifold using Navigation Agent (offloaded via Celery)."""
    try:
        try:
            from src.tasks import async_navigate
            task = async_navigate.delay(
                origin=request.origin,
                destination=request.destination,
                target_year=request.target_year,
                energy_level=request.energy_level
            )
            res = task.get(timeout=5.0)
            if res.get("success"):
                return NavigateResponse(
                    success=True,
                    path=res["path"],
                    warp_factor=res["warp_factor"],
                    divergence_risk=res["divergence_risk"],
                    geometry_tensor={
                        "warp_factor": res["warp_factor"],
                        "metric_tensor": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                        "extrinsic_curvature": [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]]
                    }
                )
        except Exception as celery_err:
            logger.warning(f"Celery task dispatch/execution failed, running synchronous fallback: {celery_err}")

        # Synchronous fallback
        nav_res = orchestrator.navigation_agent.navigate(
            origin=request.origin,
            destination=request.destination,
            target_year=request.target_year,
            energy_level=request.energy_level
        )
        
        return NavigateResponse(
            success=nav_res["success"],
            path=nav_res["path"],
            warp_factor=nav_res["warp_factor"],
            divergence_risk=nav_res["divergence_risk"],
            geometry_tensor=nav_res["geometry_tensor"]
        )
    except Exception as e:
        logger.error(f"Navigation computation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pathfinding navigation failure: {str(e)}"
        )


@app.post("/simulate", response_model=SimulateResponse)
async def simulate_spacetime(req: SimulateRequest):
    """Simulates spacetime warping for the Space-Time Navigator UI.
    Maps slider values (gravity, velocity, intensity) to Qiskit/NumPy simulation parameters."""
    logs = []
    try:
        now_year = 2026
        velocity_range = 1000
        target_year = now_year + max(1, int(req.velocity * velocity_range))
        logs.append(f"Target year: {target_year} (velocity {req.velocity:.2f}c → {abs(target_year - now_year)}yr delta)")

        logs.append(f"Gravity distortion: {req.gravity:.3f}, Field density: {req.intensity:.3f}")
        logs.append("Initializing Qiskit Spacetime Engine...")

        weighted_energy = req.intensity * (0.5 + 0.5 * req.gravity)
        logs.append(f"Computed weighted energy: {weighted_energy:.3f}")

        tensor = simulate_spacetime_metrics(target_year, weighted_energy)
        logs.append("Simulation complete.")

        warp_factor = tensor.warp_factor
        confidence = min(1.0, max(0.0, (warp_factor - 0.5) / 5.0 + 0.5 * req.intensity))
        logs.append(f"Warp factor: {warp_factor:.4f}, Path confidence: {confidence:.3f}")

        if req.origin or req.destination:
            origin_str = req.origin or "current spacetime"
            dest_str = req.destination or "target coordinate"
            logs.append(f"Path computed: {origin_str} → {dest_str}")

        return SimulateResponse(
            success=True,
            gravity_metric=req.gravity,
            velocity_metric=req.velocity,
            field_intensity=req.intensity,
            resolved_path_confidence=confidence,
            logs=logs,
            warp_factor=warp_factor,
            lapse=tensor.lapse,
            entropy_density=tensor.entropy_density,
            target_year=target_year,
        )
    except Exception as e:
        logger.error(f"Spacetime simulation failed: {e}")
        return SimulateResponse(
            success=False,
            gravity_metric=req.gravity,
            velocity_metric=req.velocity,
            field_intensity=req.intensity,
            resolved_path_confidence=0.0,
            logs=[f"Simulation failed: {str(e)}"],
        )


@app.post("/temporal/causality", dependencies=[Depends(verify_api_key)])
async def build_temporal_causality():
    """Build temporal causality chains (PRECEDED_BY, CAUSED) between Event nodes."""
    driver = neo4j_conn.get_driver()
    if not driver:
        raise HTTPException(status_code=503, detail="Neo4j unavailable")
    from src.knowledge_graph.temporal_causality import build_temporal_causality_chains
    result = build_temporal_causality_chains(driver)
    return result


from src.multi_llm import MultiLLMConsensus
from src.quantum_scheduler import QuantumJobScheduler
from pydantic import BaseModel, Field

multi_llm_consensus = MultiLLMConsensus()
quantum_scheduler = QuantumJobScheduler()

class ConsensusQueryRequest(BaseModel):
    prompt: str
    system_instruction: str = "You are an expert consensus analyzer."

class QuantumJobRequest(BaseModel):
    hardware: str
    target_year: int
    energy_level: float = 1.0

@app.post("/consensus/query", dependencies=[Depends(verify_api_key)])
async def post_consensus_query(request: ConsensusQueryRequest):
    """
    Evaluates queries against multiple active provider models, returning consensus scores.
    """
    try:
        res = await multi_llm_consensus.generate_consensus(request.prompt, request.system_instruction)
        return res
    except Exception as e:
        logger.error(f"Consensus generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consensus generation error: {str(e)}"
        )

@app.post("/quantum/schedule")
async def post_quantum_schedule(request: QuantumJobRequest):
    """
    Schedules simulated or real quantum hardware execution tasks.
    """
    try:
        # Simulate spacetime geometry to get a tensor for the job
        geometry_tensor = simulate_spacetime_metrics(request.target_year, request.energy_level)
        job_info = quantum_scheduler.submit_job(request.hardware, geometry_tensor)
        return job_info
    except Exception as e:
        logger.error(f"Quantum job scheduling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quantum scheduling error: {str(e)}"
        )

@app.get("/quantum/job/{job_id}")
async def get_quantum_job(job_id: str):
    """
    Checks status and retrieves details of a submitted quantum job.
    """
    job_info = quantum_scheduler.get_job_status(job_id)
    if job_info.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="Quantum job not found")
    return job_info

@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def post_ingest(request: IngestRequest):
    """Ingests a new markdown page or document into the Neo4j knowledge graph (offloaded via Celery)."""
    try:
        try:
            from src.tasks import async_ingest_page
            task = async_ingest_page.delay(
                title=request.title,
                content=request.content,
                tags=request.tags,
                sources=request.sources
            )
            res = task.get(timeout=5.0)
            if res.get("success"):
                from src.cache import cache_store, cache_decorator
                cache_store.invalidate_all()
                return IngestResponse(
                    success=True,
                    nodes_created=res["nodes_created"],
                    relationships_created=res["relationships_created"],
                    confidence_score=res["confidence_score"]
                )
        except Exception as celery_err:
            logger.warning(f"Celery task dispatch/execution failed, running synchronous fallback: {celery_err}")

        # Synchronous fallback
        driver = neo4j_conn.get_driver()
        nodes, rels = ingest_wiki_page(
            driver,
            title=request.title,
            content=request.content,
            default_tags=request.tags,
            default_sources=request.sources
        )
        from src.cache import cache_store, cache_decorator
        cache_store.invalidate_all()
        return IngestResponse(
            success=True,
            nodes_created=nodes,
            relationships_created=rels,
            confidence_score=0.9
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )

def _process_ingested_content(
    text: str,
    filename: Optional[str] = None,
    skip_neo4j: bool = False
) -> FileIngestResponse:
    analysis = ingest_agent.analyze_content(text, filename=filename)
    pages_created = []
    pages_updated = []
    total_nodes = 0
    total_rels = 0

    if not analysis.suggested_pages:
        return FileIngestResponse(
            success=True,
            pages_created=[],
            pages_updated=[],
            total_pages=0,
        )

    for page in analysis.suggested_pages:
        if page.confidence < settings.WIKI_MIN_CONFIDENCE:
            logger.info(f"Skipping page '{page.title}' — confidence {page.confidence:.2f} < threshold {settings.WIKI_MIN_CONFIDENCE}")
            continue
        if not settings.WIKI_AUTO_CREATE:
            logger.info(f"Skipping page creation — WIKI_AUTO_CREATE is disabled")
            break
        page_type = page.page_type
        if page_type not in ("entities", "concepts", "projects"):
            page_type = ingest_agent.classify_page_type(page.title, page.summary, page.tags)
        slug, is_new = write_page(
            title=page.title,
            body=page.body,
            tags=page.tags,
            sources=page.sources,
            related=page.related,
            page_type=page_type,
        )
        try:
            cross_reference_new_page(slug, page.title, page_type)
        except Exception as xref_err:
            logger.warning(f"Cross-reference failed for '{page.title}': {xref_err}")

        if not skip_neo4j:
            try:
                driver = neo4j_conn.get_driver()
                full_content = f"---\ntitle: {page.title}\ntags: {page.tags}\nsources: {page.sources}\nrelated: {page.related}\n---\n\n{page.body}"
                nodes, rels = ingest_wiki_page(
                    driver,
                    title=page.title,
                    content=full_content,
                    default_tags=page.tags,
                    default_sources=page.sources,
                )
                total_nodes += nodes
                total_rels += rels
            except Exception as neo4j_err:
                logger.warning(f"Neo4j ingest failed for '{page.title}': {neo4j_err}")

        if is_new:
            pages_created.append(page.title)
        else:
            pages_updated.append(page.title)

        try:
            from src.staleness_queue import record_pulse_completed
            record_pulse_completed(slug, divergence_risk=0.0, state_label="unverified")
        except Exception as queue_err:
            logger.warning(f"Failed to seed staleness queue for '{slug}': {queue_err}")

    try:
        index_entries = [(slugify(p.title), p.title, p.page_type) for p in analysis.suggested_pages if p.confidence >= settings.WIKI_MIN_CONFIDENCE]
        if index_entries:
            append_to_index(index_entries)
    except Exception as idx_err:
        logger.warning(f"Index update failed: {idx_err}")

    try:
        safe_filename = filename or 'document'
        safe_filename = re.sub(r'[\r\n#*`\[\]\(\)]', '', safe_filename)
        log_text = f"Uploaded {safe_filename}: {len(pages_created)} pages created, {len(pages_updated)} updated"
        append_to_log(log_text)
    except Exception as log_err:
        logger.warning(f"Log update failed: {log_err}")

    invalidate_index_cache()
    from src.cache import cache_store, cache_decorator
    cache_store.invalidate_all()

    return FileIngestResponse(
        success=True,
        pages_created=pages_created,
        pages_updated=pages_updated,
        total_pages=len(pages_created) + len(pages_updated),
        nodes_created=total_nodes,
        relationships_created=total_rels,
    )


@app.post("/ingest/analyze", response_model=AnalyzeResponse)
async def post_ingest_analyze(request: AnalyzeRequest):
    """Analyzes raw text content and returns suggested wiki pages without committing."""
    try:
        analysis = ingest_agent.analyze_content(request.content, filename=request.filename)
        pages = [
            SuggestedPageModel(
                title=p.title,
                page_type=p.page_type,
                tags=p.tags,
                sources=p.sources,
                summary=p.summary,
                body=p.body,
                related=p.related,
                confidence=p.confidence,
            )
            for p in analysis.suggested_pages
        ]
        return AnalyzeResponse(
            success=True,
            suggested_pages=pages,
            confidence=analysis.confidence,
            raw_text_preview=analysis.raw_text_preview,
        )
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/ingest/file", response_model=FileIngestResponse, dependencies=[Depends(verify_api_key)])
async def post_ingest_file(file: UploadFile = File(...)):
    """Uploads a single file, analyzes content via LLM, and creates/updates wiki pages + Neo4j."""
    try:
        content_bytes = await file.read()
        if len(content_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Uploaded file size exceeds the 50MB limit")
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1")

        response = _process_ingested_content(text, filename=file.filename)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")


@app.post("/ingest/folder", response_model=FolderIngestResponse, dependencies=[Depends(verify_api_key)])
async def post_ingest_folder(file: UploadFile = File(...)):
    """Uploads a zip archive of files, processes each through the ingest pipeline."""
    try:
        content_bytes = await file.read()
        if len(content_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Uploaded file size exceeds the 50MB limit")
        file_results = []
        failed_files = []
        total_created = 0
        total_updated = 0
        total_nodes = 0
        total_rels = 0
        file_count = 0

        with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
            for entry in zf.infolist():
                if entry.is_dir():
                    continue
                if not entry.filename.endswith((".md", ".txt", ".json", ".csv", ".html")):
                    continue
                try:
                    raw = zf.read(entry.filename)
                    try:
                        text = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        text = raw.decode("latin-1")
                    result = _process_ingested_content(text, filename=entry.filename)
                    file_results.append(result)
                    total_created += len(result.pages_created)
                    total_updated += len(result.pages_updated)
                    total_nodes += result.nodes_created
                    total_rels += result.relationships_created
                    file_count += 1
                except Exception as per_file_err:
                    logger.warning(f"Failed to process {entry.filename}: {per_file_err}")
                    failed_files.append({"filename": entry.filename, "error": str(per_file_err)})

        return FolderIngestResponse(
            success=True,
            total_files=file_count,
            total_pages_created=total_created,
            total_pages_updated=total_updated,
            total_nodes_created=total_nodes,
            total_relationships_created=total_rels,
            file_results=file_results,
            failed_files=failed_files,
        )
    except HTTPException:
        raise
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid zip archive")
    except Exception as e:
        logger.error(f"Folder ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Folder ingestion failed: {str(e)}")


def _run_neo4j_bulk_ingest(wiki_root: str) -> Dict[str, int]:
    """Clear Neo4j and bulk-ingest all wiki markdown pages. Returns aggregate counts."""
    subdirs = ["concepts", "entities", "projects"]
    driver = neo4j_conn.get_driver()
    total_nodes = 0
    total_rels = 0
    pages_ingested = 0

    with driver.session() as session:
        logger.info("Clearing existing Neo4j database...")
        session.run("MATCH (n) DETACH DELETE n")

    for subdir in subdirs:
        dir_path = os.path.join(wiki_root, subdir)
        if not os.path.exists(dir_path):
            logger.warning(f"Directory {dir_path} does not exist. Skipping.")
            continue
        for filename in os.listdir(dir_path):
            if not filename.endswith(".md"):
                continue
            file_path = os.path.join(dir_path, filename)
            title = os.path.splitext(filename)[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                nodes, rels = ingest_wiki_page(driver, title, content)
                total_nodes += nodes
                total_rels += rels
                pages_ingested += 1
            except Exception as page_err:
                logger.error(f"Failed to ingest page {filename}: {page_err}")

    from src.cache import cache_store, cache_decorator
    cache_store.invalidate_all()
    logger.info(f"Bulk ingestion completed. Ingested {pages_ingested} pages. Created {total_nodes} nodes, {total_rels} relationships.")
    return {
        "pages_ingested": pages_ingested,
        "nodes_created": total_nodes,
        "relationships_created": total_rels,
    }


@app.post("/ingest/pdf-folder", dependencies=[Depends(verify_api_key)])
def post_ingest_pdf_folder(req: PdfFolderIngestRequest):
    """Scan a folder of PDFs, extract text via pypdf, run the IngestAgent on each paper,
    and write resulting wiki pages to the filesystem.

    If skip_neo4j=False and dry_run=False, triggers a full Neo4j bulk rebuild at the end
    so the graph reflects all newly-created wiki pages.
    """
    from src.wiki.pdf_extract import extract_text_from_pdf, copy_pdf_to_raw

    folder_path = req.folder_path
    if not os.path.isabs(folder_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.join(project_root, folder_path)

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {req.folder_path}")

    pdf_files = sorted(
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".pdf")
    )

    pages_created: List[str] = []
    pages_updated: List[str] = []
    failed_files: List[Dict[str, str]] = []
    pdfs_processed = 0

    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        slug = slugify(os.path.splitext(filename)[0])

        try:
            raw_rel = copy_pdf_to_raw(pdf_path, slug)
            if raw_rel is None:
                failed_files.append({"filename": filename, "error": "Failed to copy PDF to wiki/raw/"})
                continue

            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                failed_files.append({"filename": filename, "error": "No extractable text (possibly scanned/image PDF)"})
                continue

            if req.dry_run:
                logger.info("Dry-run: analyzed '%s' (%d chars extracted)", filename, len(text))
                pdfs_processed += 1
                continue

            analysis = ingest_agent.analyze_content(text, filename=filename)
            for page in analysis.suggested_pages:
                if page.confidence < settings.WIKI_MIN_CONFIDENCE:
                    continue
                if page.page_type not in ("entities", "concepts", "projects"):
                    page.page_type = ingest_agent.classify_page_type(page.title, page.summary, page.tags)
                page_slug, is_new = write_page(
                    title=page.title,
                    body=page.body,
                    tags=page.tags,
                    sources=page.sources,
                    related=page.related,
                    page_type=page.page_type,
                )
                try:
                    cross_reference_new_page(page_slug, page.title, page.page_type)
                except Exception as xref_err:
                    logger.warning(f"Cross-reference failed for '{page.title}': {xref_err}")

                if is_new:
                    pages_created.append(page.title)
                else:
                    pages_updated.append(page.title)

            pdfs_processed += 1
        except Exception as exc:
            logger.error("Failed to process PDF '%s': %s", filename, exc)
            failed_files.append({"filename": filename, "error": str(exc)})

    neo4j_bulk_triggered = False
    wiki_root = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_root):
        wiki_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root)
    if not req.skip_neo4j and not req.dry_run:
        try:
            _run_neo4j_bulk_ingest(wiki_root)
            neo4j_bulk_triggered = True
        except Exception as neo4j_err:
            logger.error(f"Neo4j bulk ingest failed after PDF processing: {neo4j_err}")
            failed_files.append({"filename": "_neo4j_bulk", "error": str(neo4j_err)})

    if not req.dry_run:
        try:
            all_new_pages = [(slugify(p), p, t)
                             for t in ["entities", "concepts", "projects"]
                             for p in (pages_created + pages_updated)
                             if os.path.exists(os.path.join(wiki_root, t, f"{slugify(p)}.md"))]
            if all_new_pages:
                append_to_index([(slug, title, ptype) for slug, title, ptype in all_new_pages])
        except Exception as idx_err:
            logger.warning(f"Index update failed: {idx_err}")

        try:
            summary = (f"Ingested {pdfs_processed}/{len(pdf_files)} PDFs from {req.folder_path}: "
                       f"{len(pages_created)} pages created, {len(pages_updated)} updated, "
                       f"{len(failed_files)} failures")
            append_to_log(summary)
        except Exception as log_err:
            logger.warning(f"Log update failed: {log_err}")

        invalidate_index_cache()
        from src.cache import cache_store, cache_decorator
        cache_store.invalidate_all()

    return PdfFolderIngestResponse(
        success=True,
        total_pdfs=len(pdf_files),
        pdfs_processed=pdfs_processed,
        pages_created=pages_created,
        pages_updated=pages_updated,
        failed_files=failed_files,
        dry_run=req.dry_run,
        neo4j_bulk_triggered=neo4j_bulk_triggered,
    )


from fastapi import WebSocket, WebSocketDisconnect
import asyncio

_ws_conversations: Dict[int, str] = {}

@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent responses and status updates.
    """
    await websocket.accept()
    ws_id = id(websocket)
    conversation_id = _ws_conversations.get(ws_id)
    if not conversation_id:
        import uuid
        conversation_id = str(uuid.uuid4())
        _ws_conversations[ws_id] = conversation_id
    try:
        while True:
            # Wait for incoming messages from the client
            data = await websocket.receive_text()
            logger.info(f"WebSocket received query: {data}")
            
            from src.idle_sentinel import IdleSentinel
            IdleSentinel.update_activity("websocket")
            
            # Start a span for tracing this WebSocket interaction
            with tracer.start_as_current_span("ws_agent_query"):
                # Track execution in metrics
                agent_loop_counter.add(1)
                
                # Send acknowledgement/status
                await websocket.send_json({"status": "processing", "message": "Initiating search..."})
                await asyncio.sleep(0.1)
                
                # Retrieve prior conversation turns from Redis
                history: List[Dict[str, str]] = []
                try:
                    from src.cache import cache_store, cache_decorator
                    raw = cache_store.get(_conversation_redis_key(conversation_id))
                    if raw:
                        history = json.loads(raw)
                except Exception as e:
                    logger.warning(f"Failed to retrieve WebSocket conversation history: {e}")

                # Execute query via orchestrator with history
                output = await orchestrator.execute(data, history=history)
                response = _build_query_response(data, output, conversation_id=conversation_id, history=history)
                
                # Stream parts of the response
                answer = response.answer
                chunks = answer.split(" ")
                for i, chunk in enumerate(chunks):
                    await websocket.send_json({
                        "status": "streaming",
                        "chunk": chunk + (" " if i < len(chunks) - 1 else "")
                    })
                    await asyncio.sleep(0.05)
                    
                await websocket.send_json({
                    "status": "completed",
                    "answer": answer,
                    "confidence": response.confidence,
                    "entities": response.entities,
                    "sources": response.sources,
                    "conversation_id": conversation_id,
                    "history": response.history,
                })
                
                # Store updated conversation
                updated_history = history + [
                    {"role": "user", "content": data},
                    {"role": "assistant", "content": answer},
                ]
                try:
                    cache_store.set(_conversation_redis_key(conversation_id), json.dumps(updated_history[-20:]), ttl=604800)
                except Exception as e:
                    logger.warning(f"Failed to store WebSocket conversation: {e}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except Exception as e:
            logger.warning(f"Failed to send WebSocket error message: {e}")


def reconcile_neo4j_with_wiki(driver):
    """Prunes Neo4j nodes that were deleted from the wiki filesystem."""
    try:
        wiki_root = settings.WIKI_DATA_DIR
        if not os.path.isabs(wiki_root):
            wiki_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root)
            
        valid_slugs = set()
        for subdir in ["entities", "concepts", "projects"]:
            dir_path = os.path.join(wiki_root, subdir)
            if os.path.isdir(dir_path):
                for fname in os.listdir(dir_path):
                    if fname.endswith(".md"):
                        valid_slugs.add(fname[:-3].lower())
                        
        with driver.session() as session:
            result = session.run("MATCH (n:Entity) RETURN n.name as name, n.tags as tags, n.confidence as confidence")
            orphans = []
            for record in result:
                name = record["name"]
                if not name:
                    continue
                slug = slugify(name)
                tags = record["tags"]
                confidence = record["confidence"]
                
                # If it's not a placeholder, check if it has a corresponding wiki page
                has_page = slug in valid_slugs
                is_placeholder = (not tags) and (confidence is not None and confidence < 1.0)
                
                if not has_page and not is_placeholder:
                    orphans.append(name)
                    
            if orphans:
                logger.info(f"Reconciliation: Found {len(orphans)} orphaned Neo4j nodes. Pruning: {orphans}")
                session.run("MATCH (n:Entity) WHERE n.name IN $names DETACH DELETE n", names=orphans)
                from src.cache import cache_store, cache_decorator
                cache_store.invalidate_all()
    except Exception as e:
        logger.warning(f"Failed to reconcile Neo4j with wiki: {e}")


@app.get("/search")
async def search_endpoint(q: str = Query(..., min_length=2), limit: int = Query(20, le=100)):
    """Full-text search across all entities using Neo4j fulltext index. Returns scored results."""
    driver = neo4j_conn.get_driver()
    if not driver:
        return {"results": [], "query": q, "total": 0}
    results = fulltext_search(driver, q, limit)
    return {"results": results, "query": q, "total": len(results)}


@app.get("/entities")
async def get_entities(exclude_fallback: bool = True):
    """Retrieves all Lore Entities from the Neo4j database.
    When exclude_fallback=True (default), low-quality fallback pages are hidden."""
    import uuid
    driver = neo4j_conn.get_driver()
    if driver:
        reconcile_neo4j_with_wiki(driver)
    fallback_filter = "WHERE (n.fallback IS NULL OR n.fallback <> true)" if exclude_fallback else ""
    query = f"""
    MATCH (n:Entity)
    {fallback_filter}
    RETURN n
    """
    entities = []
    try:
        with driver.session() as session:
            res = session.run(query)
            for record in res:
                node = record["n"]
                name = node.get("name", "Unknown")
                node_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
                labels = list(node.labels)
                node_type = "Entity"
                for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
                    if label in labels:
                        node_type = label
                        break
                
                node_sources = node.get("sources", [])
                if not isinstance(node_sources, list):
                    node_sources = [str(node_sources)] if node_sources else []
                node_sources = [str(s) for s in node_sources]

                entities.append({
                    "id": node_uuid,
                    "name": name,
                    "type": node_type,
                    "summary": node.get("content_preview", node.get("summary", "")),
                    "confidence": node.get("confidence", 1.0),
                    "source": node_sources[0] if node_sources else "Unknown",
                    "sources": node_sources
                })
        return entities
    except Exception as e:
        logger.error(f"Failed to fetch entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/time")
async def get_server_time():
    """Returns the server's current date, time, and timezone."""
    from datetime import datetime, timezone
    now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    return {
        "iso8601": now.isoformat(),
        "unix": now.timestamp(),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": str(now.astimezone().tzinfo),
        "utc_offset": now.astimezone().strftime("%z"),
        "utc_iso8601": utc_now.isoformat(),
    }


# SSE event broadcasting for real-time index notifications
_sse_clients: set[asyncio.Queue] = set()
_sse_lock = asyncio.Lock()


async def _sse_broadcast(event_type: str, entity_name: str, source: str = ""):
    """Broadcast an index change event to all connected SSE clients."""
    message = {
        "type": event_type,
        "entity": entity_name,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    async with _sse_lock:
        stale = set()
        for q in _sse_clients:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                stale.add(q)
        _sse_clients -= stale


@app.get("/events/stream")
async def sse_event_stream(request: Request):
    """SSE endpoint for real-time index change notifications.
    Clients connect via EventSource or similar and receive JSON events
    whenever an entity is created, updated, or deleted."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    async with _sse_lock:
        _sse_clients.add(queue)
    try:
        async def generate():
            try:
                while True:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            except asyncio.CancelledError:
                pass
        return StreamingResponse(generate(), media_type="text/event-stream")
    finally:
        async with _sse_lock:
            _sse_clients.discard(queue)


@app.get("/status/progress")
async def get_progress():
    """Returns real-time progress of all background operations
    (reconciliation, idle ingestion, chat ingest, fallback retry,
    wiki watcher, LLM engine, knowledge graph counters)."""
    from src.progress_tracker import get_all
    return get_all()


@app.delete("/entities/{name}", dependencies=[Depends(verify_api_key)])
async def delete_entity(name: str, hard: bool = True, force: bool = False):
    """Deletes a lore entity. Coordinates with filesystem to delete the matching wiki page if it exists."""
    slug = slugify(name)
    found_subdir = None
    for subdir in ["entities", "concepts", "projects"]:
        try:
            if read_page(slug, subdir) is not None:
                found_subdir = subdir
                break
        except Exception:
            pass
            
    if found_subdir:
        logger.info(f"Coordinating deletion of entity '{name}' with wiki page '{slug}' in {found_subdir}")
        # Delegate to delete_wiki_page to handle backups, link cleaning, and Neo4j deletion
        await delete_wiki_page(slug=slug, page_type=found_subdir, hard=hard, force=force)
        return {"success": True, "deleted": True, "wiki_deleted": True}
        
    try:
        driver = neo4j_conn.get_driver()
        if not driver:
            return {"success": False, "deleted": False, "wiki_deleted": False}
        with driver.session() as session:
            result = session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n RETURN count(n)", name=name)
            count = result.single()[0]
            if count == 0 and slug != name:
                result = session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n RETURN count(n)", name=slug)
                count = result.single()[0]
            logger.info(f"Deleted entity '{name}' directly from Neo4j (nodes removed: {count})")
            return {"success": True, "deleted": count > 0, "wiki_deleted": False}
    except Exception as e:
        logger.error(f"Failed to delete entity '{name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@cache_decorator(prefix="neo4j", ttl=60)
def query_events(driver):
    query = """
    MATCH (e:Event)
    RETURN e.name AS name,
           e.display_name AS display_name,
           e.date AS date,
           e.tags AS tags,
           e.sources AS sources,
           e.content_preview AS preview,
           e.confidence AS confidence,
           labels(e) AS labels
    ORDER BY e.date ASC
    """
    events = []
    with driver.session() as session:
        res = session.run(query)
        for record in res:
            node_labels = [l.lower() for l in record["labels"]]
            tags = [t.lower() for t in record["tags"] or []]
            name = record["name"]
            name_lower = name.lower() if name else ""
            title = record["display_name"] or name

            event_type = "anomaly"
            if "crash" in name_lower or "recovery" in name_lower:
                event_type = "crash"
            elif "testimony" in name_lower or "whistleblower" in name_lower:
                event_type = "testimony"
            elif "theory" in name_lower or "propulsion" in name_lower:
                event_type = "theory"

            node_sources = record["sources"] or []
            if not isinstance(node_sources, list):
                node_sources = [str(node_sources)] if node_sources else []

            events.append({
                "id": name,
                "title": title,
                "description": record["preview"] or "",
                "date": record["date"],
                "confidence": record["confidence"] or 1.0,
                "source": str(node_sources[0]) if node_sources else "Unknown",
                "type": event_type,
                "sources": [str(s) for s in node_sources],
            })
    return events


@app.get("/events")
async def get_events():
    """Retrieves all Event-labeled nodes from Neo4j with their stored dates."""
    driver = neo4j_conn.get_driver()
    if not driver:
        return {"events": []}
    if driver:
        reconcile_neo4j_with_wiki(driver)
    try:
        events = query_events(driver)
        return {"events": events}
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/bulk", dependencies=[Depends(verify_api_key)])
def post_ingest_bulk():
    """Clears the Neo4j database and bulk-ingests all wiki markdown pages."""
    try:
        import os
        wiki_root = settings.WIKI_DATA_DIR
        if not os.path.isabs(wiki_root):
            wiki_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root)
        subdirs = ["concepts", "entities", "projects"]
        
        driver = neo4j_conn.get_driver()
        with driver.session() as session:
            logger.info("Clearing existing Neo4j database...")
            session.run("MATCH (n) DETACH DELETE n")
            
        total_nodes = 0
        total_rels = 0
        pages_ingested = 0
        
        for subdir in subdirs:
            dir_path = os.path.join(wiki_root, subdir)
            if not os.path.exists(dir_path):
                logger.warning(f"Directory {dir_path} does not exist. Skipping.")
                continue
                
            for filename in os.listdir(dir_path):
                if filename.endswith(".md"):
                    file_path = os.path.join(dir_path, filename)
                    title = os.path.splitext(filename)[0]
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        nodes, rels = ingest_wiki_page(driver, title, content)
                        total_nodes += nodes
                        total_rels += rels
                        pages_ingested += 1
                    except Exception as page_err:
                        logger.error(f"Failed to ingest page {filename}: {page_err}")
                        
        # Invalidate Redis/memory cache
        from src.cache import cache_store, cache_decorator
        cache_store.invalidate_all()
        
        logger.info(f"Bulk ingestion completed. Ingested {pages_ingested} pages. Created {total_nodes} nodes, {total_rels} relationships.")
        return {
            "success": True,
            "pages_ingested": pages_ingested,
            "nodes_created": total_nodes,
            "relationships_created": total_rels
        }
    except Exception as e:
        logger.error(f"Bulk ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wiki/clear-content", response_model=WikiClearResponse, dependencies=[Depends(verify_api_key)])
def post_wiki_clear_content(confirm: bool = False):
    """Deletes all CONTENT/SUBJECT wiki pages (UFO/alien/time-travel knowledge),
    preserves CODE/ENGINEERING pages (project architecture, tools, infrastructure).
    Pages with `protected: true` in frontmatter are never deleted."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is a highly destructive operation. Please provide the 'confirm=true' query parameter to proceed."
        )
    try:
        from src.wiki.cleanup import clear_content_pages
        result = clear_content_pages(dry_run=False)

        if result.get("success"):
            try:
                driver = neo4j_conn.get_driver()
                if driver:
                    import os
                    wiki_root = settings.WIKI_DATA_DIR
                    if not os.path.isabs(wiki_root):
                        wiki_root = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root
                        )
                    subdirs = ["concepts", "entities", "projects"]
                    with driver.session() as session:
                        session.run("MATCH (n) DETACH DELETE n")
                    for subdir in subdirs:
                        dir_path = os.path.join(wiki_root, subdir)
                        if not os.path.exists(dir_path):
                            continue
                        for filename in os.listdir(dir_path):
                            if filename.endswith(".md"):
                                file_path = os.path.join(dir_path, filename)
                                title = os.path.splitext(filename)[0]
                                try:
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        content = f.read()
                                    from src.knowledge_graph.ingest import ingest_wiki_page
                                    ingest_wiki_page(driver, title, content)
                                except Exception as page_err:
                                    logger.warning(f"Re-ingest failed for {filename}: {page_err}")
            except Exception as neo4j_err:
                logger.warning(f"Neo4j re-ingest skipped: {neo4j_err}")

        return WikiClearResponse(**result)
    except Exception as e:
        logger.error(f"Wiki clear content failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wiki/export", response_model=WikiExportResponse)
async def get_wiki_export():
    """Exports the entire wiki directory as a zip file."""
    try:
        from src.wiki.backup import export_wiki
        filepath = export_wiki()
        if not filepath:
            raise HTTPException(status_code=500, detail="Failed to create wiki export")
        page_count = 0
        for subdir in ["entities", "concepts", "projects"]:
            d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wiki", subdir)
            if os.path.isdir(d):
                page_count += len([f for f in os.listdir(d) if f.endswith(".md")])
        size_kb = round(os.path.getsize(filepath) / 1024, 1)
        return WikiExportResponse(success=True, filepath=filepath, size_kb=size_kb, page_count=page_count)
    except Exception as e:
        logger.error(f"Wiki export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wiki/import", response_model=WikiImportResponse, dependencies=[Depends(verify_api_key)])
async def post_wiki_import(file: UploadFile = File(...)):
    """Imports a wiki zip file and restores the wiki directory."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        from src.wiki.backup import import_wiki
        restored = import_wiki(tmp_path)

        os.unlink(tmp_path)

        if restored == 0:
            raise HTTPException(status_code=400, detail="No pages could be restored from the uploaded file. Ensure it is a valid wiki export zip.")

        try:
            driver = neo4j_conn.get_driver()
            if driver:
                with driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
                for subdir in ["concepts", "entities", "projects"]:
                    dir_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wiki", subdir)
                    if not os.path.exists(dir_path):
                        continue
                    for filename in os.listdir(dir_path):
                        if filename.endswith(".md"):
                            title = os.path.splitext(filename)[0]
                            try:
                                with open(os.path.join(dir_path, filename), "r") as f:
                                    content = f.read()
                                from src.knowledge_graph.ingest import ingest_wiki_page
                                ingest_wiki_page(driver, title, content)
                            except Exception as page_err:
                                logger.warning(f"Re-ingest failed for {filename}: {page_err}")
        except Exception as neo4j_err:
            logger.warning(f"Neo4j re-ingest after import skipped: {neo4j_err}")

        from src.wiki.writer import invalidate_index_cache
        invalidate_index_cache()
        from src.cache import cache_store, cache_decorator
        cache_store.invalidate_all()

        return WikiImportResponse(success=True, restored_count=restored)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wiki import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wiki/backups")
async def list_wiki_backups(subdir: str = "auto"):
    """Lists available wiki backups."""
    from src.wiki.backup import list_backups
    return {"backups": list_backups(subdir=subdir)}


@app.post("/wiki/backup/now")
async def create_wiki_backup_now():
    """Creates an immediate wiki snapshot."""
    from datetime import datetime
    from src.wiki.backup import create_snapshot
    path = create_snapshot(name=f"manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    return {"success": path is not None, "filepath": path}


@app.post("/neo4j/backup", dependencies=[Depends(verify_api_key)])
async def create_neo4j_backup():
    """Triggers a Neo4j database dump. Stops container, dumps, restarts."""
    from src.neo4j_backup import create_backup
    path = create_backup()
    return {"success": path is not None, "filepath": str(path) if path else None}


@app.get("/neo4j/backups")
async def list_neo4j_backups():
    """Lists available Neo4j dump files."""
    from src.neo4j_backup import list_backups
    return {"backups": list_backups()}


@app.post("/neo4j/restore/{dump_name}", dependencies=[Depends(verify_api_key)])
async def restore_neo4j_backup(dump_name: str):
    """Restores Neo4j from a dump file. Stops container, loads, restarts."""
    from src.neo4j_backup import restore_backup
    success = restore_backup(dump_name)
    return {"success": success, "message": "Restored from dump" if success else "Restore failed"}


@app.post("/wiki/reconcile-stop", dependencies=[Depends(verify_api_key)])
async def set_reconciliation_stop():
    """Sets a stop signal for long-running reconciliation. Reconciliation checks
    this signal between pages and exits early."""
    from src.reconciliation_gate import set_reconciliation_stop as _set_stop
    _set_stop()
    return {"success": True, "message": "Reconciliation stop signal set"}


@app.post("/wiki/reconcile")
async def trigger_reconciliation():
    """Triggers reconciliation of all wiki pages. Safe to call even if
    reconciliation is already running — returns immediately if busy."""
    loop = asyncio.get_event_loop()
    from src.wiki.watcher import reconcile_existing_pages
    loop.run_in_executor(None, reconcile_existing_pages)
    return {"success": True, "message": "Reconciliation dispatched to background thread"}


@app.get("/wiki/pages", response_model=WikiPageListResponse)
async def get_wiki_pages(page_type: Optional[str] = None):
    """Lists all wiki pages with frontmatter metadata. Optionally filter by page_type."""
    wiki_root = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_root):
        wiki_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root)
    subdirs = ["entities", "concepts", "projects"]
    if page_type:
        subdirs = [s for s in subdirs if s == page_type]
    pages = []
    for subdir in subdirs:
        dir_path = os.path.join(wiki_root, subdir)
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith(".md"):
                continue
            slug = fname[:-3]
            page_data = read_page(slug, subdir)
            if not page_data:
                continue
            fm = page_data["frontmatter"]
            try:
                pages.append(WikiPageListItem(
                    slug=slug,
                    title=fm.get("title", slug),
                    page_type=subdir,
                    tags=fm.get("tags", []),
                    created=str(fm.get("created", "")),
                    updated=str(fm.get("updated", "")),
                    protected=fm.get("protected", False),
                ))
            except Exception as e:
                logger.warning(f"Skipping page {slug}/{subdir} due to validation error: {e}")
    return WikiPageListResponse(success=True, pages=pages, total=len(pages))


@app.get("/wiki/page/{slug:path}", response_model=WikiPageDetailResponse)
async def get_wiki_page(slug: str, page_type: str = "entities"):
    """Returns full detail for a single wiki page."""
    page_data = read_page(slug, page_type)
    if not page_data:
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found in {page_type}")
    fm = page_data["frontmatter"]
    return WikiPageDetailResponse(
        success=True,
        slug=slug,
        title=fm.get("title", slug),
        page_type=page_type,
        tags=fm.get("tags", []),
        sources=fm.get("sources", []),
        related=fm.get("related", []),
        body=page_data["body"],
        created=fm.get("created", ""),
        updated=fm.get("updated", ""),
        protected=fm.get("protected", False),
    )


@app.delete("/wiki/page/{slug:path}", response_model=WikiDeleteResponse, dependencies=[Depends(verify_api_key)])
async def delete_wiki_page(slug: str, page_type: str = "entities", hard: bool = False, force: bool = False):
    """Deletes a single wiki page file. Protected pages cannot be deleted unless forced (only lore pages can be forced)."""
    page_data = read_page(slug, page_type)
    if not page_data:
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found in {page_type}")
    fm = page_data["frontmatter"]
    title = fm.get("title", slug)

    if fm.get("protected", False):
        from src.wiki.cleanup import ENGINEERING_TAGS
        tags = set(fm.get("tags", []))
        is_engineering = (page_type == "projects") or bool(tags & ENGINEERING_TAGS)
        if is_engineering:
            raise HTTPException(status_code=403, detail=f"Wiki page '{title}' is a core engineering/project file and cannot be deleted.")
        if not force:
            raise HTTPException(status_code=403, detail=f"Wiki page '{title}' is protected. Use the 'force=true' parameter to delete this content page.")

    # Create pre-deletion backup snapshot
    from src.wiki.backup import create_snapshot
    try:
        create_snapshot(name="auto")
    except Exception as snap_err:
        logger.warning(f"Pre-deletion snapshot failed: {snap_err}")

    deleted = delete_page(slug, page_type)
    if not deleted:
        raise HTTPException(status_code=500, detail=f"Failed to delete wiki page '{slug}'")

    neo4j_cleaned = False
    try:
        driver = neo4j_conn.get_driver()
        if driver:
            with driver.session() as session:
                result = session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n RETURN count(n)", name=title)
                count = result.single()[0]
                if count == 0 and slug != title:
                    result = session.run("MATCH (n:Entity {name: $name}) DETACH DELETE n RETURN count(n)", name=slug)
                    count = result.single()[0]
                if count > 0:
                    neo4j_cleaned = True
                    logger.info(f"Deleted Neo4j node for '{title}' ({count} nodes removed)")
    except Exception as e:
        logger.warning(f"Neo4j cleanup skipped for deleted page '{title}': {e}")

    cross_refs_cleaned = 0
    if hard:
        wiki_root = settings.WIKI_DATA_DIR
        if not os.path.isabs(wiki_root):
            wiki_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), wiki_root)
            
        def clean_obsidian_links(body_text: str, target_slug: str, target_title: str) -> tuple[str, bool]:
            link_pattern = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
            modified = False
            
            def repl(match):
                nonlocal modified
                link_target = match.group(1).strip()
                alias = match.group(2)
                
                # Match against slug, title, case insensitively and slugified
                if (slugify(link_target) == slugify(target_slug) or 
                    slugify(link_target) == slugify(target_title) or 
                    link_target.lower() == target_title.lower() or 
                    link_target.lower() == target_slug.lower()):
                    modified = True
                    if alias:
                        return alias.strip()
                    else:
                        return link_target
                return match.group(0)
                
            new_body = link_pattern.sub(repl, body_text)
            return new_body, modified

        try:
            for subdir in ["entities", "concepts", "projects"]:
                dir_path = os.path.join(wiki_root, subdir)
                if not os.path.isdir(dir_path):
                    continue
                for fname in os.listdir(dir_path):
                    if not fname.endswith(".md"):
                        continue
                    fslug = fname[:-3]
                    if fslug == slug:
                        continue
                    pdata = read_page(fslug, subdir)
                    if not pdata:
                        continue
                    
                    # 1. Clean related frontmatter field
                    rel = set(pdata["frontmatter"].get("related", []))
                    removed_rel = False
                    for ref in list(rel):
                        if slugify(ref) == slug or ref == title or ref.lower() == title.lower() or slugify(ref) == slugify(title):
                            rel.discard(ref)
                            removed_rel = True
                            
                    # 2. Clean Obsidian links from body text
                    new_body, removed_body = clean_obsidian_links(pdata["body"], slug, title)
                    
                    if removed_rel or removed_body:
                        write_page(
                            title=pdata["frontmatter"].get("title", fslug),
                            body=new_body,
                            tags=pdata["frontmatter"].get("tags", []),
                            sources=pdata["frontmatter"].get("sources", []),
                            related=list(rel),
                            page_type=subdir,
                        )
                        cross_refs_cleaned += 1
        except Exception as e:
            logger.warning(f"Cross-reference cleanup failed: {e}")

    invalidate_index_cache()
    append_to_log(f"Deleted wiki page: {title} ({page_type}/{slug})")

    return WikiDeleteResponse(
        success=True,
        slug=slug,
        page_type=page_type,
        title=title,
        neo4j_cleaned=neo4j_cleaned,
        cross_refs_cleaned=cross_refs_cleaned,
    )


@app.get("/debug/routing")
async def debug_routing(query: str = ""):
    """
    Debug endpoint: runs the classification step only and returns the routing decision
    without executing the full pipeline. Useful for understanding why a query
    routes to a particular agent node.
    """
    if not query:
        return {"error": "Provide a query parameter, e.g. ?query=plot+timelines+element+115"}

    parsed = orchestrator.query_agent.classify_and_parse(query)

    wiki_matches = []
    try:
        from src.agents.query_agent import _wiki_entity_lookup
        wiki_matches = _wiki_entity_lookup(query)
    except Exception as e:
        logger.debug(f"Wiki entity lookup failed during debug classify: {e}")

    return {
        "query": query,
        "parsed_query": parsed.model_dump(),
        "wiki_matches": wiki_matches,
        "routed_to": "ResearchNode" if parsed.intent != "navigate" and parsed.intent != "status" else
                     ("NavigateNode" if parsed.intent == "navigate" else "StatusNode"),
        "confidence_gated": parsed.confidence < 0.6,
    }


# ── Living Almanac endpoints ─────────────────────────────────────────────

class PulseRequest(BaseModel):
    handles: Optional[Dict[str, Any]] = None


@app.post("/pulse/purge-empty", dependencies=[Depends(verify_api_key)])
async def purge_empty_pulses(entity_name: Optional[str] = None):
    """Deletes pulse snapshot JSON and MD files with zero evidence items.
    If entity_name is provided, only deletes empty snapshots for that entity.
    """
    try:
        from src.wiki.paths import get_pulse_dir
        from src.wiki.pulse_writer import load_pulse_snapshot, list_pulse_snapshots
        from src.wiki.writer import slugify

        pulse_dir = get_pulse_dir()
        if not pulse_dir.exists():
            return {"purged_count": 0, "status": "success"}

        if entity_name:
            slug = slugify(entity_name)
            pattern = f"{slug}-*.json"
            candidates = list(pulse_dir.glob(pattern))
        else:
            candidates = list(pulse_dir.glob("*.json"))

        purged = 0
        for json_path in candidates:
            data = load_pulse_snapshot(json_path)
            if data and data.get("evidence_count", 0) == 0:
                json_path.unlink(missing_ok=True)
                md_path = json_path.with_suffix(".md")
                md_path.unlink(missing_ok=True)
                purged += 1

        return {"purged_count": purged, "status": "success"}
    except Exception as e:
        logger.error(f"Purge empty pulses failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pulse/{entity_name}", response_model=AsyncTaskResponse, dependencies=[Depends(verify_api_key)])
async def post_pulse(entity_name: str, background_tasks: BackgroundTasks, request: PulseRequest = None):
    entity_name = _validate_entity_name(entity_name)
    handles = None
    if request and request.handles:
        handles = request.handles

    task = task_registry.create_task(f"Pulse: {entity_name}")

    async def execute_pulse_async():
        try:
            task.log(f"Starting pulse for '{entity_name}'...")
            task.update_progress(0.1)

            from src.agents.pulse_agent import PulseAgent
            agent = PulseAgent()

            task.log("Contacting last30days evidence collector...")
            task.update_progress(0.3)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent.run_pulse, entity_name, handles)

            if result.status == "error":
                task.log(f"Pulse execution reported error: {result.error or 'Unknown CLI error'}")
                task.set_failed(result.error or "CLI execution failed")
            else:
                task.log(f"Pulse succeeded! Ingested {len(result.evidence)} evidence items.")
                task.log(f"Remaining monthly budget: ${result.budget_remaining:.2f}")
                task.update_progress(1.0)
                task.set_success(result)
        except Exception as e:
            logger.error(f"Async pulse failed for '{entity_name}': {e}", exc_info=True)
            task.set_failed(str(e))

    asyncio.ensure_future(execute_pulse_async())
    return AsyncTaskResponse(
        task_id=task.id,
        status=task.status,
        message=f"Pulse task for '{entity_name}' initiated in background."
    )


@app.get("/entities/{name}/divergence", response_model=DivergenceResult)
async def get_entity_divergence(name: str):
    name = _validate_entity_name(name, "entity_name")
    slug = slugify(name)
    wiki_page = read_page(slug, "entities") or read_page(slug, "concepts") or read_page(slug, "projects")
    if not wiki_page:
        raise HTTPException(status_code=404, detail=f"Wiki page for entity '{name}' not found")

    try:
        from src.wiki.pulse_writer import load_recent_pulse_evidence
        fresh_evidence = load_recent_pulse_evidence(name, max_age_days=14)
    except Exception as e:
        logger.debug(f"Failed to load pulse evidence for divergence: {e}")
        fresh_evidence = []

    try:
        from src.quantum_credibility.divergence_engine import compute_narrative_divergence
        result = compute_narrative_divergence(name, wiki_page, fresh_evidence)
        return result
    except Exception as e:
        logger.error(f"Divergence computation failed for '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Divergence computation failed: {str(e)}")


@app.get("/timeline")
async def get_global_timeline(start_date: str = None, end_date: str = None, limit: int = 100):
    """Get all dated Event nodes from the graph for timeline visualization."""
    driver = neo4j_conn.get_driver()
    if not driver:
        return {"events": [], "total": 0}
    events = get_temporal_events(driver, start_date, end_date, limit)
    return {"events": events, "total": len(events)}


@app.get("/timeline/range")
async def get_timeline_range_endpoint():
    """Get the earliest and latest dates across all Event nodes."""
    driver = neo4j_conn.get_driver()
    if not driver:
        return {"earliest": None, "latest": None, "total": 0}
    return get_timeline_range(driver)


@app.get("/entities/{name}/temporal-context")
async def get_entity_temporal(name: str):
    """Get the temporal neighborhood of an entity — events connected to it."""
    name = _validate_entity_name(name, "entity_name")
    driver = neo4j_conn.get_driver()
    if not driver:
        return {"events": []}
    events = get_entity_temporal_context(driver, name)
    return {"entity": name, "events": events, "total": len(events)}


@app.get("/entities/{name}/timeline")
async def get_entity_timeline(name: str, days: int = 30):
    name = _validate_entity_name(name, "entity_name")
    try:
        from src.almanac.timeline import build_timeline
        timeline_result = build_timeline(name, days=days)
        return {
            "entity_name": name,
            "days": days,
            "points": [p.model_dump() for p in timeline_result.points],
            "total": len(timeline_result.points),
        }
    except Exception as e:
        logger.error(f"Timeline build failed for '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Timeline build failed: {str(e)}")


@app.get("/entities/{name}/entanglement")
async def get_entity_entanglement(name: str, candidate: Optional[str] = None, limit: int = 10):
    name = _validate_entity_name(name, "entity_name")
    try:
        from src.wiki.pulse_writer import load_recent_pulse_evidence
        evidence = load_recent_pulse_evidence(name, max_age_days=30)
    except Exception:
        evidence = []

    if not evidence:
        return {
            "entity_name": name,
            "entanglements": [],
            "total": 0,
            "note": "No recent pulse evidence found — run a pulse first",
        }

    try:
        from src.quantum_credibility.entanglement_corr import compute_entanglement_correlation, compute_all_entanglements

        if candidate:
            res = compute_entanglement_correlation(name, candidate, evidence)
            return {
                "entity_name": name,
                "entanglements": [res],
                "total": 1,
            }
        else:
            all_res = compute_all_entanglements(name, evidence)
            return {
                "entity_name": name,
                "entanglements": all_res[:limit],
                "total": len(all_res),
            }
    except Exception as e:
        logger.error(f"Entanglement computation failed for '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Entanglement computation failed: {str(e)}")


class TribunalRequest(BaseModel):
    claim_text: str = Field(..., min_length=1)
    divergence_risk: float = Field(0.0, ge=0.0, le=1.0)


@app.post("/entities/{name}/tribunal")
async def post_entity_tribunal(name: str, request: TribunalRequest):
    name = _validate_entity_name(name, "entity_name")
    try:
        from src.wiki.pulse_writer import load_recent_pulse_evidence
        evidence = load_recent_pulse_evidence(name, max_age_days=30)
    except Exception:
        evidence = []

    # Also try to get wavefunction score for the claim
    wavefunction = {"state_label": "contested", "epistemic_confidence": 0.5, "social_traction": 0.0}

    try:
        from src.quantum_credibility.wavefunction import ClaimWavefunction
        wf = ClaimWavefunction()
        if evidence:
            cc = wf.score_claim(request.claim_text, evidence[:20])
            wavefunction = {
                "state_label": cc.state_label,
                "epistemic_confidence": cc.epistemic_confidence,
                "social_traction": cc.social_traction,
                "collapsed": cc.collapsed,
                "evidence_count": cc.evidence_count,
                "scoring_inputs": cc.scoring_inputs,
            }
    except Exception as e:
        logger.debug(f"Wavefunction scoring for tribunal failed: {e}")

    try:
        from src.agents.tribunal_agent import TribunalAgent
        agent = TribunalAgent()
        result = agent.run_tribunal(
            claim_text=request.claim_text,
            evidence=evidence[:30] if evidence else [],
            wavefunction=wavefunction,
            divergence_risk=request.divergence_risk,
        )
        return result
    except Exception as e:
        logger.error(f"Tribunal failed for '{name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tribunal failed: {str(e)}")


@app.get("/budget/status", response_model=BudgetStatus)
async def get_budget_status():
    try:
        from src.budget import budget_tracker
        return budget_tracker.get_status()
    except Exception as e:
        logger.error(f"Budget status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Budget status failed: {str(e)}")


@app.post("/budget/approve", dependencies=[Depends(verify_api_key)])
async def post_budget_approve():
    try:
        from src.budget import budget_tracker
        status = budget_tracker.approve_hold()
        return {"success": True, "budget": status.model_dump()}
    except Exception as e:
        logger.error(f"Budget approve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Budget approve failed: {str(e)}")


@app.post("/research/{thread_id}/approve", dependencies=[Depends(verify_api_key)])
async def post_research_approve(thread_id: str):
    try:
        from src.agents.research_agent import ResearchAgent, research_graph
        config = {"configurable": {"thread_id": thread_id}}
        current_state = research_graph.get_state(config)
        if not current_state or not current_state.values:
            raise HTTPException(status_code=404, detail=f"No paused research found for thread '{thread_id}'")
        if not current_state.next:
            raise HTTPException(status_code=400, detail=f"Research thread '{thread_id}' is not paused")

        query = current_state.values.get("query", "")
        entities = current_state.values.get("entities", [])
        history = current_state.values.get("history", [])

        updated_values = dict(current_state.values)
        updated_values["human_approved"] = True
        research_graph.update_state(config, updated_values)

        # Resume graph execution — runs human_approval_gate → context_assembly
        final_state = research_graph.invoke(None, config=config)

        # Generate summary from the assembled context
        agent = ResearchAgent()
        summary = agent._generate_summary(
            query=query,
            context=final_state.get("assembled_context", ""),
            history=history,
        )

        return {
            "success": True,
            "thread_id": thread_id,
            "summary": summary,
            "entities": [e for e in entities if e],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research approve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research approve failed: {str(e)}")


@app.get("/system/ingestion/status")
async def get_ingestion_status():
    from src.scheduler import get_almanac_status, _IDLE_LAST_RUN, _IDLE_CHECK_INTERVAL_SECONDS
    from src.cache import cache_store, cache_decorator
    queue_size = 0
    next_batch = []
    try:
        if cache_store.redis_client:
            queue_size = cache_store.redis_client.zcard("staleness:queue") or 0
            next_batch_raw = cache_store.redis_client.zrevrange("staleness:queue", 0, 2)
            next_batch = [
                el.decode() if isinstance(el, bytes) else el
                for el in next_batch_raw
            ]
    except Exception:
        pass
    almanac = get_almanac_status()
    return {
        "almanac_enabled": almanac.get("enabled"),
        "almanac_last_run": almanac.get("last_run"),
        "almanac_running": almanac.get("running"),
        "staleness_queue_size": queue_size,
        "staleness_next_batch": next_batch,
        "check_interval_seconds": _IDLE_CHECK_INTERVAL_SECONDS,
    }


@app.post("/almanac/generate", response_model=AsyncTaskResponse)
async def post_almanac_generate(background_tasks: BackgroundTasks, dry_run: bool = True):
    task = task_registry.create_task("Almanac Generation")

    async def execute_almanac_async():
        try:
            task.log(f"Initializing Daily Almanac Generation (dry_run={dry_run})...")
            task.update_progress(0.1)

            from src.almanac.almanac_generator import generate_daily_almanac

            task.log("Analyzing active wiki entities...")
            task.update_progress(0.2)

            task.log("Running scheduled pulses & narrative analysis (this may take a few seconds)...")
            task.update_progress(0.5)

            result = await generate_daily_almanac(dry_run=dry_run)

            task.log(f"Almanac generation completed. Status: {result.status}")
            if result.error:
                task.log(f"Generator warnings: {result.error}")

            task.log(f"Processed {result.entities_processed} entities.")
            task.log(f"Wavefunctions: {result.claims_collapsed} collapsed, {result.newly_contested} newly contested.")

            if result.html_path:
                task.log(f"HTML brief compiled: {result.html_path}")
            if result.md_path:
                task.log(f"Markdown brief compiled: {result.md_path}")

            task.update_progress(1.0)
            task.set_success(result)
        except Exception as e:
            logger.error(f"Async almanac generation failed: {e}", exc_info=True)
            task.set_failed(str(e))

    asyncio.ensure_future(execute_almanac_async())
    return AsyncTaskResponse(
        task_id=task.id,
        status=task.status,
        message="Almanac generation task initiated in background."
    )


@app.get("/almanac/summary")
async def get_almanac_summary():
    """Returns top contested claims and newly moved entities from the latest almanac."""
    try:
        from src.wiki.paths import get_almanac_dir as _get_ad
        ad = _get_ad()
        if not ad.exists():
            return {"date": None, "contested_claims": [], "newly_contested": 0, "entities_processed": []}

        md_files = sorted(ad.glob("*.md"), reverse=True)
        if not md_files:
            return {"date": None, "contested_claims": [], "newly_contested": 0, "entities_processed": []}
        latest = md_files[0]
        with open(latest, "r", encoding="utf-8") as f:
            content = f.read()
        contested = re.findall(r"- \*\*contested\*\*.*: (.+)", content)
        entities = re.findall(r"^## (.+)$", content, re.MULTILINE)
        entities_processed = [e for e in entities if not e.startswith("State of the Anomaly")]
        return {
            "date": latest.stem,
            "contested_claims": contested[:10],
            "newly_contested": len(contested),
            "entities_processed": entities_processed,
        }
    except Exception as e:
        logger.error(f"Almanac summary failed: {e}")
        return {"date": None, "contested_claims": [], "newly_contested": 0, "entities_processed": []}


@app.get("/almanac/history")
async def get_almanac_history(limit: int = 20):
    try:
        from src.wiki.paths import get_almanac_dir as _get_ad
        ad = _get_ad()
        if not ad.exists():
            return {"almanacs": [], "total": 0}

        html_files = sorted(ad.glob("*.html"), reverse=True)
        results = []
        for f in html_files[:limit]:
            try:
                stat = f.stat()
                from datetime import datetime as _dt, timezone as _tz
                results.append({
                    "date": f.stem,
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created": _dt.fromtimestamp(stat.st_mtime, tz=_tz.utc).isoformat(),
                })
            except Exception:
                continue

        return {"almanacs": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Almanac history failed: {e}")
        return {"almanacs": [], "total": 0}


@app.get("/pulse/history")
async def get_pulse_history(entity_name: Optional[str] = None, limit: int = 50):
    try:
        from src.wiki.paths import get_pulse_dir
        from src.wiki.pulse_writer import list_pulse_snapshots, load_pulse_snapshot

        pulse_dir = get_pulse_dir()
        if not pulse_dir.exists():
            return {"pulses": [], "total": 0}

        files = list(reversed(list_pulse_snapshots(entity_name))) if entity_name else sorted(pulse_dir.glob("*.json"), reverse=True)

        latest: Dict[str, Dict[str, Any]] = {}
        for f in files:
            data = load_pulse_snapshot(f)
            if not data:
                continue
            ename = data.get("entity_name", f.stem)
            if ename not in latest:
                evidence_trimmed = data.get("evidence", [])[:10]
                latest[ename] = {
                    "entity_name": ename,
                    "date": data.get("date", ""),
                    "timestamp": data.get("timestamp", ""),
                    "evidence_count": data.get("evidence_count", 0),
                    "evidence": evidence_trimmed,
                    "file": str(f),
                }

        pulses = list(latest.values())[:limit]
        empty_count = sum(1 for p in pulses if p["evidence_count"] == 0)

        return {
            "pulses": pulses,
            "total": len(pulses),
            "unique_entities": len(latest),
            "empty_count": empty_count,
        }
    except Exception as e:
        logger.error(f"Pulse history failed: {e}")
        return {"pulses": [], "total": 0}



@app.get("/almanac/file/{date}")
async def get_almanac_file(date: str):
    """Retrieves the HTML content of a specific daily almanac brief."""
    from src.wiki.paths import get_almanac_dir
    ad = get_almanac_dir()
    filepath = ad / f"{date}.html"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Almanac file for date '{date}' not found")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"date": date, "content": content}
    except Exception as e:
        logger.error(f"Failed to read almanac file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read almanac file: {str(e)}")


@app.get("/pulse/snapshot")
async def get_pulse_snapshot(filepath: str):
    """Retrieves the full JSON data of a pulse snapshot by file path."""
    from pathlib import Path
    p = Path(filepath)
    if not p.exists() or not filepath.endswith(".json"):
        raise HTTPException(status_code=404, detail="Snapshot file not found")
    try:
        from src.wiki.pulse_writer import load_pulse_snapshot
        data = load_pulse_snapshot(p)
        if not data:
            raise HTTPException(status_code=404, detail="Could not parse pulse snapshot")
        return data
    except Exception as e:
        logger.error(f"Failed to load snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/drafts", dependencies=[Depends(verify_api_key)])
async def get_entities_drafts():
    """Lists all entity drafts proposed in the system."""
    try:
        from src.discovery_agent import list_drafts
        return list_drafts()
    except Exception as e:
        logger.error(f"Failed to list drafts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/entities/{slug}/promote", dependencies=[Depends(verify_api_key)])
async def post_entity_promote(slug: str):
    """Promotes an entity draft to published wiki entities."""
    try:
        from src.discovery_agent import promote_draft
        success = promote_draft(slug)
        if not success:
            raise HTTPException(status_code=404, detail=f"Draft '{slug}' not found or promotion failed")
        return {"success": True, "slug": slug}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote draft '{slug}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


