import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from src.config import settings

logger = logging.getLogger("chickensoup.discovery")

# Cache of the active provider (used for agent requests)
_discovered_provider: Optional[str] = None
_discovered_base_url: Optional[str] = None
_discovered_models: List[str] = []

# Cache of ALL providers probed during last discovery
_discovered_all: Dict[str, dict] = {}

_URL_MAPPING = {
    "omlx": settings.OMLX_API_URL,
    "ollama": settings.OLLAMA_API_URL,
    "lmstudio": settings.LMSTUDIO_API_URL,
}

_PROBE_TIMEOUT = 5.0


def _probe_single(name: str) -> dict:
    """Probe one provider, return {base_url, models, available}."""
    base_url = _URL_MAPPING.get(name.lower())
    if not base_url:
        return {"base_url": "", "models": [], "available": False}

    clean_url = base_url.rstrip("/")
    models_url = f"{clean_url}/models"

    try:
        req = urllib.request.Request(models_url, method="GET")
        with urllib.request.urlopen(req, timeout=_PROBE_TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = _extract_models(data)
                logger.info(f"Probed {name} — available with models: {models}")
                return {"base_url": clean_url, "models": models, "available": True}
    except Exception as e:
        logger.debug(f"Probed {name} — unreachable: {e}")

    return {"base_url": clean_url, "models": [], "available": False}


def refresh_discovery() -> Tuple[str, str, List[str]]:
    """
    Probe ALL providers in the fallback chain and return the first
    available one (by preference order).  Updates both the active cache
    and the full provider map.
    """
    global _discovered_provider, _discovered_base_url, _discovered_models, _discovered_all

    # If user has explicitly set a provider override, probe only that one
    if settings.LLM_ACTIVE_PROVIDER:
        name = settings.LLM_ACTIVE_PROVIDER.lower()
        result = _probe_single(name)
        _discovered_all = {name: result}
        if result["available"]:
            _discovered_provider = name
            _discovered_base_url = result["base_url"]
            _discovered_models = result["models"]
            return name, result["base_url"], result["models"]
        logger.warning(f"Configured provider '{name}' unreachable — falling through")

    # Probe all providers in the fallback chain
    providers = settings.fallback_chain_list
    all_results: Dict[str, dict] = {}
    for provider in providers:
        all_results[provider] = _probe_single(provider)

    _discovered_all = all_results

    # Pick the first available from the preference order
    for provider in providers:
        entry = all_results.get(provider, {})
        if entry.get("available"):
            _discovered_provider = provider
            _discovered_base_url = entry["base_url"]
            _discovered_models = entry["models"]
            logger.info(f"Auto-selected {provider} with models: {entry['models']}")
            return provider, entry["base_url"], entry["models"]

    logger.warning("No active local LLM provider discovered. Falling back to simulated/mock provider.")
    _discovered_provider = "simulated"
    _discovered_base_url = "http://localhost:8000/mock/v1"
    _discovered_models = ["mock-gpt-4", "mock-llama-3"]
    return _discovered_provider, _discovered_base_url, _discovered_models


def _extract_models(data) -> List[str]:
    """Extract model IDs from OpenAI-compatible /v1/models response."""
    if isinstance(data, dict) and "data" in data:
        return [m["id"] for m in data["data"] if isinstance(m, dict) and "id" in m]
    elif isinstance(data, list):
        return [m.get("id", m.get("name")) for m in data if isinstance(m, dict)]
    return []


def get_discovered(depth: str = "cached") -> Tuple[str, str, List[str]]:
    """Return cached active-provider info, re-probing if 'depth' is 'fresh'."""
    if depth == "fresh" or _discovered_provider is None:
        return refresh_discovery()
    return _discovered_provider, _discovered_base_url, _discovered_models


def get_active_model() -> str:
    """Return the configured model if compatible with the active provider, otherwise the first discovered model."""
    provider, _, models = get_discovered()
    if settings.LLM_ACTIVE_PROVIDER and settings.LLM_ACTIVE_PROVIDER.lower() == provider:
        if settings.LLM_ACTIVE_MODEL:
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
    """Return the full map of {provider_name: {base_url, models, available}}.
    Re-probes if cache is empty."""
    if not _discovered_all:
        refresh_discovery()
    return dict(_discovered_all)


def probe_provider(name: str) -> Tuple[str, str, List[str]]:
    """
    Probe a specific provider without updating the global cache.
    Returns (provider, base_url, models) or ('simulated', base_url, []).
    """
    result = _probe_single(name)
    if result["available"]:
        return name, result["base_url"], result["models"]
    return "simulated", result["base_url"], []


def discover_active_provider() -> Tuple[str, str, List[str]]:
    """Return cached active-provider info, re-probing only if not yet cached."""
    return get_discovered("cached")
