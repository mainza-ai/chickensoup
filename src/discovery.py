import json
import logging
import threading
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from src.config import settings

logger = logging.getLogger("chickensoup.discovery")

# ──────────────────────────────────────────────
# Cache of the active provider (used for agent requests)
# ──────────────────────────────────────────────
_discovered_provider: Optional[str] = None
_discovered_base_url: Optional[str] = None
_discovered_models: List[str] = []

# Cache of ALL providers probed during last discovery
_discovered_all: Dict[str, dict] = {}

# ──────────────────────────────────────────────
# TTL cache metadata
# ──────────────────────────────────────────────
_CACHE_TTL = 300.0  # 5 minutes
_discovered_at: float = 0.0
_cache_lock = threading.Lock()

# ──────────────────────────────────────────────
# Circuit breaker state per provider
# States: closed | open | half-open
# ──────────────────────────────────────────────
_CIRCUIT_COOLDOWN = 120.0  # seconds
_CIRCUIT_FAILURE_THRESHOLD = 5

@dataclass
class _CircuitState:
    state: str = "closed"  # closed | open | half-open
    failures: int = 0
    opened_at: float = 0.0

_circuit_breakers: Dict[str, _CircuitState] = {}


# ──────────────────────────────────────────────
# URL Mapping
# ──────────────────────────────────────────────
_URL_MAPPING = {
    "omlx": settings.OMLX_API_URL,
    "ollama": settings.OLLAMA_API_URL,
    "lmstudio": settings.LMSTUDIO_API_URL,
}

_PROBE_TIMEOUT = 5.0
_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY = 1.0
_RETRY_MAX_DELAY = 8.0

# OpenAI-compatible model-listing endpoints to try in order
_MODEL_PATHS = ["/v1/models", "/models"]


# ──────────────────────────────────────────────
# Retry helper
# ──────────────────────────────────────────────
def _retry_delay(attempt: int) -> float:
    import random
    delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
    jitter = random.uniform(-0.25, 0.25) * delay
    return max(0.1, delay + jitter)


# ──────────────────────────────────────────────
# Circuit breaker helper
# ──────────────────────────────────────────────
def _circuit_should_skip(name: str) -> bool:
    now = time.monotonic()
    cb = _circuit_breakers.setdefault(name, _CircuitState())
    if cb.state == "open":
        if now - cb.opened_at >= _CIRCUIT_COOLDOWN:
            cb.state = "half-open"
            return False
        return True
    return False


def _circuit_record_success(name: str) -> None:
    cb = _circuit_breakers.setdefault(name, _CircuitState())
    cb.state = "closed"
    cb.failures = 0


def _circuit_record_failure(name: str) -> None:
    cb = _circuit_breakers.setdefault(name, _CircuitState())
    cb.failures += 1
    if cb.failures >= _CIRCUIT_FAILURE_THRESHOLD:
        cb.state = "open"
        cb.opened_at = time.monotonic()
        logger.warning(f"Circuit breaker OPEN for provider '{name}' after {cb.failures} failures.")


# ──────────────────────────────────────────────
# Model extraction
# ──────────────────────────────────────────────
def _extract_models(data) -> List[str]:
    """Extract model IDs from OpenAI-compatible /v1/models response."""
    if isinstance(data, dict) and "data" in data:
        return [m["id"] for m in data["data"] if isinstance(m, dict) and "id" in m]
    elif isinstance(data, list):
        return [m.get("id", m.get("name")) for m in data if isinstance(m, dict)]
    return []


# ──────────────────────────────────────────────
# Single-provider probe (with retry + path fallback + circuit breaker)
# ──────────────────────────────────────────────
def _probe_single(name: str) -> dict:
    """Probe one provider, return {base_url, models, available, error}."""
    base_url = _URL_MAPPING.get(name.lower())
    if not base_url:
        return {
            "base_url": "",
            "models": [],
            "available": False,
            "error": f"Unknown provider '{name}': not in _URL_MAPPING",
        }

    if _circuit_should_skip(name):
        return {
            "base_url": base_url.rstrip("/"),
            "models": [],
            "available": False,
            "error": f"Circuit breaker open for '{name}' (cooldown active)",
        }

    clean_url = base_url.rstrip("/")
    probe_base = clean_url
    if probe_base.endswith("/v1"):
        probe_base = probe_base[:-3]

    last_exc: Optional[Exception] = None
    for path in _MODEL_PATHS:
        models_url = f"{probe_base}{path}"
        for attempt in range(_RETRY_ATTEMPTS):
            try:
                req = urllib.request.Request(models_url, method="GET")
                with urllib.request.urlopen(req, timeout=_PROBE_TIMEOUT) as response:
                    if response.status == 200:
                        raw = response.read().decode("utf-8")
                        data = json.loads(raw)
                        models = _extract_models(data)
                        logger.info(f"Probed {name} at {models_url} — available with models: {models}")
                        _circuit_record_success(name)
                        return {
                            "base_url": clean_url,
                            "models": models,
                            "available": True,
                            "error": None,
                        }
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Try next path
                    break
                last_exc = e
                logger.debug(f"Probed {name} at {models_url} — HTTP {e.code}: {e.reason}")
                break  # do not retry on HTTP 4xx/5xx (config error, not transient)
            except Exception as e:
                last_exc = e
                logger.debug(f"Probed {name} at {models_url} — attempt {attempt + 1}/{_RETRY_ATTEMPTS} failed: {e}")
                if attempt < _RETRY_ATTEMPTS - 1:
                    time.sleep(_retry_delay(attempt))

    failure_msg = str(last_exc) if last_exc else "HTTP 404 on all model paths"
    _circuit_record_failure(name)
    logger.debug(f"Probed {name} — unavailable: {failure_msg}")
    return {
        "base_url": clean_url,
        "models": [],
        "available": False,
        "error": failure_msg,
    }


# ──────────────────────────────────────────────
# Refresh discovery (with preferred-first + fallback chain)
# ──────────────────────────────────────────────
def refresh_discovery() -> Tuple[str, str, List[str]]:
    """
    Probe providers and return the first available one.
    - If LLM_ACTIVE_PROVIDER is set: probe it first (preferred-first).
      If it fails, fall through to the chain.
    - Then walk LLM_FALLBACK_CHAIN in order, return first available.
    - If none available, return ('simulated', ...).
    """
    global _discovered_provider, _discovered_base_url, _discovered_models, _discovered_all
    global _discovered_at

    with _cache_lock:
        providers = settings.fallback_chain_list
        all_results: Dict[str, dict] = {}

        # ── Preferred-first override ─────────────────────────────
        override_name = settings.LLM_ACTIVE_PROVIDER.strip().lower()
        if override_name:
            logger.info(f"Probing preferred provider '{override_name}'...")
            all_results[override_name] = _probe_single(override_name)
            if all_results[override_name]["available"]:
                _apply_result(override_name, all_results[override_name])
                logger.info(f"Using preferred provider '{override_name}'.")
                return override_name, _discovered_base_url, _discovered_models
            logger.warning(
                f"Preferred provider '{override_name}' unreachable: "
                f"{all_results[override_name].get('error')} — falling through to chain"
            )

        # ── Fallback chain ───────────────────────────────────────
        for provider in providers:
            if provider in all_results:
                continue  # already probed as override
            all_results[provider] = _probe_single(provider)

        _discovered_all = all_results

        for provider in providers:
            entry = all_results.get(provider, {})
            if entry.get("available"):
                _apply_result(provider, entry)
                logger.info(f"Auto-selected {provider} with models: {entry['models']}")
                return provider, _discovered_base_url, _discovered_models

        # ── Simulated fallback ───────────────────────────────────
        logger.warning("No active local LLM provider discovered. Falling back to simulated/mock provider.")
        _apply_result("simulated", {
            "base_url": "http://localhost:8000/mock/v1",
            "models": ["mock-gpt-4", "mock-llama-3"],
            "available": True,
            "error": None,
        })
        return _discovered_provider, _discovered_base_url, _discovered_models


def _apply_result(name: str, result: dict) -> None:
    """Update module-level globals and cache timestamp."""
    global _discovered_provider, _discovered_base_url, _discovered_models, _discovered_all, _discovered_at
    _discovered_provider = name
    _discovered_base_url = result.get("base_url", "")
    _discovered_models = result.get("models", [])
    _discovered_at = time.monotonic()


# ──────────────────────────────────────────────
# Cached/fresh accessors
# ──────────────────────────────────────────────
def get_discovered(depth: str = "cached") -> Tuple[str, str, List[str]]:
    """Return cached active-provider info, re-probing if 'depth' is 'fresh' or TTL expired."""
    if depth == "fresh":
        return refresh_discovery()

    with _cache_lock:
        if _discovered_provider is None or (time.monotonic() - _discovered_at) >= _CACHE_TTL:
            return refresh_discovery()
        return _discovered_provider, _discovered_base_url, _discovered_models


def get_active_model() -> str:
    """Return the configured model if compatible with the active provider, otherwise the first discovered model."""
    provider, _, models = get_discovered()
    if override_name := settings.LLM_ACTIVE_PROVIDER.strip().lower():
        if override_name == provider and settings.LLM_ACTIVE_MODEL:
            if not models or settings.LLM_ACTIVE_MODEL in models:
                return settings.LLM_ACTIVE_MODEL
    return models[0] if models else "default-model"


def get_active_provider() -> str:
    """Return the actual active provider being used (resolved from discovery)."""
    provider, _, _ = get_discovered()
    return provider


def get_active_base_url() -> str:
    """Return the base URL for the actual active provider being used."""
    _, url, _ = get_discovered()
    return url


def get_all_providers() -> Dict[str, dict]:
    """Return the full map of {provider_name: {base_url, models, available, error, circuit_state}}.
    Re-probes if cache is empty or TTL expired."""
    with _cache_lock:
        if not _discovered_all or (time.monotonic() - _discovered_at) >= _CACHE_TTL:
            refresh_discovery()
        raw = dict(_discovered_all)
    return {
        name: {
            "base_url": info.get("base_url", ""),
            "models": info.get("models", []),
            "available": info.get("available", False),
            "error": info.get("error"),
            "circuit_state": _circuit_breakers.get(name, _CircuitState()).state,
        }
        for name, info in raw.items()
    }


def probe_provider(name: str) -> Tuple[str, str, List[str], Optional[str]]:
    """
    Probe a specific provider without updating the global cache.
    Returns (provider, base_url, models, error).
    """
    result = _probe_single(name)
    if result["available"]:
        return name, result["base_url"], result["models"], result.get("error")
    return "simulated", result.get("base_url", ""), [], result.get("error")


def discover_active_provider() -> Tuple[str, str, List[str]]:
    """Return cached active-provider info, re-probing only if not yet cached or TTL expired."""
    return get_discovered("cached")


# ──────────────────────────────────────────────
# Health monitor (started once; daemon thread)
# ──────────────────────────────────────────────
_health_monitor_running = False
_health_monitor_lock = threading.Lock()


def _start_health_monitor() -> None:
    """Start a background daemon thread that monitors the active provider."""
    global _health_monitor_running
    with _health_monitor_lock:
        if _health_monitor_running:
            return
        _health_monitor_running = True

    def _monitor() -> None:
        failure_streak = 0
        max_streak = 3
        while True:
            time.sleep(30.0)
            try:
                provider, _, models = get_discovered()
                if provider == "simulated":
                    failure_streak = 0
                    continue
                result = _probe_single(provider)
                if result["available"]:
                    failure_streak = 0
                else:
                    failure_streak += 1
                    logger.warning(
                        f"Health check: active provider '{provider}' unavailable "
                        f"(streak {failure_streak}/{max_streak}): {result.get('error')}"
                    )
                    if failure_streak >= max_streak:
                        logger.warning(
                            f"Active provider '{provider}' failed {max_streak} consecutive health checks; "
                            "invalidating cache and re-discovering."
                        )
                        _invalidate_cache()
                        refresh_discovery()
                        failure_streak = 0
            except Exception as e:
                logger.debug(f"Health monitor loop error: {e}")

    t = threading.Thread(target=_monitor, daemon=True, name="llm-health-monitor")
    t.start()
    logger.info("LLM health monitor started (30s interval).")


def _invalidate_cache() -> None:
    """Force next get_discovered() call to re-probe."""
    global _discovered_provider, _discovered_at
    with _cache_lock:
        _discovered_provider = None
        _discovered_at = 0.0


# Try to start the health monitor lazily on first access
_health_monitor_lazy_started = False


def _lazy_start_health_monitor() -> None:
    global _health_monitor_lazy_started
    if not _health_monitor_lazy_started:
        _health_monitor_lazy_started = True
        try:
            _start_health_monitor()
        except Exception as e:
            logger.debug(f"Health monitor lazy start failed: {e}")


# Wrap public accessors to lazily start the monitor on first call
_original_get_discovered = get_discovered


def _wrapped_get_discovered(depth: str = "cached") -> Tuple[str, str, List[str]]:
    _lazy_start_health_monitor()
    return _original_get_discovered(depth)


# Replace the module-level reference so callers get the wrapped version
# while internal code can still call the original if needed.
get_discovered = _wrapped_get_discovered  # type: ignore[misc]
