import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from src.config import settings

logger = logging.getLogger("chickensoup.discovery")

# In-memory cache of the last successful discovery
_discovered_provider: Optional[str] = None
_discovered_base_url: Optional[str] = None
_discovered_models: List[str] = []

def refresh_discovery() -> Tuple[str, str, List[str]]:
    """
    Probes local LLM provider endpoints in order of preference: oMLX -> Ollama -> LM Studio.
    Updates the in-memory cache and returns (provider_name, base_url, list_of_models).
    """
    global _discovered_provider, _discovered_base_url, _discovered_models

    # If user has explicitly set a provider override, skip probing entirely
    if settings.LLM_ACTIVE_PROVIDER:
        url_mapping = {
            "omlx": settings.OMLX_API_URL,
            "ollama": settings.OLLAMA_API_URL,
            "lmstudio": settings.LMSTUDIO_API_URL
        }
        base_url = url_mapping.get(settings.LLM_ACTIVE_PROVIDER.lower())
        if base_url:
            clean_url = base_url.rstrip("/")
            models_url = f"{clean_url}/models"
            try:
                req = urllib.request.Request(models_url, method="GET")
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        models = _extract_models(data)
                        logger.info(f"Discovered provider '{settings.LLM_ACTIVE_PROVIDER}' with models: {models}")
                        _discovered_provider = settings.LLM_ACTIVE_PROVIDER
                        _discovered_base_url = clean_url
                        _discovered_models = models
                        return _discovered_provider, _discovered_base_url, _discovered_models
            except Exception as e:
                logger.warning(f"Configured provider '{settings.LLM_ACTIVE_PROVIDER}' unreachable: {e}")

    # Standard fallback chain probing
    providers = settings.fallback_chain_list
    url_mapping = {
        "omlx": settings.OMLX_API_URL,
        "ollama": settings.OLLAMA_API_URL,
        "lmstudio": settings.LMSTUDIO_API_URL
    }

    for provider in providers:
        base_url = url_mapping.get(provider.lower())
        if not base_url:
            continue

        clean_url = base_url.rstrip("/")
        models_url = f"{clean_url}/models"

        logger.info(f"Probing {provider} at {models_url}...")
        try:
            req = urllib.request.Request(models_url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = _extract_models(data)
                    logger.info(f"Successfully discovered {provider} with models: {models}")
                    _discovered_provider = provider
                    _discovered_base_url = clean_url
                    _discovered_models = models
                    return _discovered_provider, _discovered_base_url, _discovered_models
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
            logger.debug(f"{provider} probe failed: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error probing {provider}: {e}")
            continue

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
    """
    Returns cached discovery result, re-probing if 'depth' is 'fresh'.
    This avoids redundant HTTP probes on every status check.
    """
    if depth == "fresh" or _discovered_provider is None:
        return refresh_discovery()
    return _discovered_provider, _discovered_base_url, _discovered_models


def get_active_model() -> str:
    """Returns the user-configured model, or the first discovered model, or a fallback."""
    if settings.LLM_ACTIVE_MODEL:
        return settings.LLM_ACTIVE_MODEL
    _, _, models = get_discovered()
    return models[0] if models else "default-model"


def get_active_provider() -> str:
    """Returns the user-configured provider, or the discovered provider."""
    if settings.LLM_ACTIVE_PROVIDER:
        return settings.LLM_ACTIVE_PROVIDER
    provider, _, _ = get_discovered()
    return provider


def probe_provider(name: str) -> Tuple[str, str, List[str]]:
    """
    Probe a specific provider by name and return (provider, base_url, models).
    Does NOT update the global discovery cache — use refresh_discovery() for that.
    Returns ('simulated', base_url, []) if the provider is unreachable.
    """
    url_mapping = {
        "omlx": settings.OMLX_API_URL,
        "ollama": settings.OLLAMA_API_URL,
        "lmstudio": settings.LMSTUDIO_API_URL,
    }
    base_url = url_mapping.get(name.lower())
    if not base_url:
        return "simulated", "", []

    clean_url = base_url.rstrip("/")
    models_url = f"{clean_url}/models"

    try:
        req = urllib.request.Request(models_url, method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = _extract_models(data)
                logger.info(f"probe_provider: {name} available with models: {models}")
                return name, clean_url, models
    except Exception as e:
        logger.debug(f"probe_provider: {name} unreachable: {e}")

    return "simulated", clean_url, []

def get_active_base_url() -> str:
    """Return the base URL for the current active provider (live, not cached)."""
    if settings.LLM_ACTIVE_PROVIDER:
        mapping = {
            "omlx": settings.OMLX_API_URL,
            "ollama": settings.OLLAMA_API_URL,
            "lmstudio": settings.LMSTUDIO_API_URL,
        }
        url = mapping.get(settings.LLM_ACTIVE_PROVIDER.lower())
        if url:
            return url.rstrip("/")
    _, url, _ = get_discovered()
    return url

# Backward-compatible alias for existing callers
discover_active_provider = refresh_discovery
