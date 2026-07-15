import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from src.config import settings

logger = logging.getLogger("chickensoup.discovery")

_CACHE_PROVIDER: Optional[str] = None
_CACHE_BASE_URL: Optional[str] = None
_CACHE_MODELS: List[str] = []
_CACHE_ALL: Dict[str, dict] = {}

_LOCAL_URLS = {
    "omlx": settings.OMLX_API_URL,
    "ollama": settings.OLLAMA_API_URL,
    "lmstudio": settings.LMSTUDIO_API_URL,
}

_CLOUD_PROVIDERS = {
    "nvidia": {
        "base_url": settings.NVIDIA_API_URL,
        "api_key": settings.NVIDIA_API_KEY,
        "models": [
            "nvidia/nemotron-3-super-120b-a12b",
            "meta/llama-3.1-405b-instruct",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "nvidia/nemotron-4-340b-instruct",
        ],
    },
    "openrouter": {
        "base_url": settings.OPENROUTER_API_URL,
        "api_key": settings.OPENROUTER_API_KEY,
        "models": [],
    },
    "custom": {
        "base_url": settings.CUSTOM_LLM_API_URL,
        "api_key": settings.CUSTOM_LLM_API_KEY,
        "models": [m.strip() for m in settings.CUSTOM_LLM_MODELS.split(",") if m.strip()],
    },
}

_PROBE_TIMEOUT = 5.0


def _probe_local(name: str) -> dict:
    base_url = _LOCAL_URLS.get(name.lower())
    if not base_url:
        return {"base_url": "", "models": [], "available": False, "type": "local"}
    clean_url = base_url.rstrip("/")
    models_url = f"{clean_url}/models"
    try:
        req = urllib.request.Request(models_url, method="GET")
        with urllib.request.urlopen(req, timeout=_PROBE_TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = _extract_models(data)
                logger.info(f"Probed {name} — available with models: {models}")
                return {"base_url": clean_url, "models": models, "available": True, "type": "local"}
    except Exception as e:
        logger.debug(f"Probed {name} — unreachable: {e}")
    return {"base_url": clean_url, "models": [], "available": False, "type": "local"}


def _probe_cloud(name: str) -> dict:
    info = _CLOUD_PROVIDERS.get(name.lower())
    if not info:
        return {"base_url": "", "models": [], "available": False, "type": "cloud"}
    clean_url = info["base_url"].rstrip("/")
    api_key = info.get("api_key", "")
    if not api_key:
        logger.debug(f"Cloud provider {name} has no API key configured — skipping")
        return {"base_url": clean_url, "models": info.get("models", []), "available": False, "type": "cloud"}
    try:
        req = urllib.request.Request(f"{clean_url}/models", method="GET")
        req.add_header("Authorization", f"Bearer {api_key}")
        with urllib.request.urlopen(req, timeout=_PROBE_TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = _extract_models(data) or info.get("models", [])
                logger.info(f"Probed {name} — available with models: {models}")
                return {"base_url": clean_url, "models": models, "available": True, "type": "cloud", "api_key": api_key}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            logger.warning(f"{name} returned 401 — invalid API key")
        elif e.code == 403:
            logger.warning(f"{name} returned 403 — forbidden")
        else:
            logger.debug(f"{name} HTTP error {e.code}: {e}")
    except Exception as e:
        logger.debug(f"Probed {name} — unreachable: {e}")
    # Even if probe fails, if we have an API key and known models, still consider it available
    fallback_models = info.get("models", [])
    if api_key and fallback_models:
        logger.info(f"{name} probe failed but has API key and known models — marking available")
        return {"base_url": clean_url, "models": fallback_models, "available": True, "type": "cloud", "api_key": api_key}
    return {"base_url": clean_url, "models": info.get("models", []), "available": False, "type": "cloud"}


def refresh_discovery() -> Tuple[str, str, List[str]]:
    global _CACHE_PROVIDER, _CACHE_BASE_URL, _CACHE_MODELS, _CACHE_ALL
    if settings.LLM_ACTIVE_PROVIDER:
        name = settings.LLM_ACTIVE_PROVIDER.lower()
        result = _probe_provider_by_name(name)
        _CACHE_ALL = {name: result}
        if result.get("available"):
            _CACHE_PROVIDER = name
            _CACHE_BASE_URL = result["base_url"]
            _CACHE_MODELS = result.get("models", [])
            return name, result["base_url"], result.get("models", [])
        logger.warning(f"Configured provider '{name}' unreachable — falling through")
    providers = settings.fallback_chain_list
    all_results: Dict[str, dict] = {}
    for provider in providers:
        all_results[provider] = _probe_provider_by_name(provider)
    _CACHE_ALL = all_results
    for provider in providers:
        entry = all_results.get(provider, {})
        if entry.get("available"):
            _CACHE_PROVIDER = provider
            _CACHE_BASE_URL = entry["base_url"]
            _CACHE_MODELS = entry.get("models", [])
            logger.info(f"Auto-selected {provider} with models: {entry.get('models', [])}")
            return provider, entry["base_url"], entry.get("models", [])
    logger.warning("No active LLM provider discovered. Falling back to simulated/mock provider.")
    _CACHE_PROVIDER = "simulated"
    _CACHE_BASE_URL = "http://localhost:8000/mock/v1"
    _CACHE_MODELS = ["mock-gpt-4", "mock-llama-3"]
    return _CACHE_PROVIDER, _CACHE_BASE_URL, _CACHE_MODELS


def _probe_provider_by_name(name: str) -> dict:
    if name.lower() in _LOCAL_URLS:
        return _probe_local(name)
    if name.lower() in _CLOUD_PROVIDERS:
        return _probe_cloud(name)
    return {"base_url": "", "models": [], "available": False}


def _extract_models(data) -> List[str]:
    if isinstance(data, dict) and "data" in data:
        return [m["id"] for m in data["data"] if isinstance(m, dict) and "id" in m]
    elif isinstance(data, list):
        return [m.get("id", m.get("name")) for m in data if isinstance(m, dict)]
    return []


def get_discovered(depth: str = "cached") -> Tuple[str, str, List[str]]:
    if depth == "fresh" or _CACHE_PROVIDER is None:
        return refresh_discovery()
    return _CACHE_PROVIDER, _CACHE_BASE_URL, _CACHE_MODELS


def get_active_model() -> str:
    provider, _, models = get_discovered()
    if settings.LLM_ACTIVE_PROVIDER and settings.LLM_ACTIVE_PROVIDER.lower() == provider:
        if settings.LLM_ACTIVE_MODEL:
            return settings.LLM_ACTIVE_MODEL
    return models[0] if models else "default-model"


def get_active_provider() -> str:
    provider, _, _ = get_discovered()
    return provider


def get_active_base_url() -> str:
    _, url, _ = get_discovered()
    return url


def get_all_providers() -> Dict[str, dict]:
    if not _CACHE_ALL:
        refresh_discovery()
    return dict(_CACHE_ALL)


def probe_provider(name: str) -> Tuple[str, str, List[str]]:
    result = _probe_provider_by_name(name)
    if result.get("available"):
        return name, result["base_url"], result.get("models", [])
    return "simulated", result.get("base_url", ""), []


def discover_active_provider() -> Tuple[str, str, List[str]]:
    return get_discovered("cached")


def get_cloud_api_key(name: str) -> str:
    info = _CLOUD_PROVIDERS.get(name.lower())
    if info:
        return info.get("api_key", "")
    return ""
