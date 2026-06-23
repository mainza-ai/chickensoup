import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from src.config import settings

logger = logging.getLogger("chickensoup.discovery")

def discover_active_provider() -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Probes local LLM provider endpoints in order of preference: oMLX -> Ollama -> LM Studio.
    Returns:
        Tuple of (provider_name, base_url, list_of_models)
    """
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
        
        # Strip trailing slash if present
        clean_url = base_url.rstrip("/")
        models_url = f"{clean_url}/models"
        
        logger.info(f"Probing {provider} at {models_url}...")
        try:
            req = urllib.request.Request(models_url, method="GET")
            # Set a low timeout of 1.5 seconds for discovery
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = []
                    # Standard OpenAI /v1/models response contains a 'data' array of objects with 'id'
                    if isinstance(data, dict) and "data" in data:
                        models = [m["id"] for m in data["data"] if isinstance(m, dict) and "id" in m]
                    elif isinstance(data, list):
                        models = [m.get("id", m.get("name")) for m in data if isinstance(m, dict)]
                    
                    logger.info(f"Successfully discovered {provider} with models: {models}")
                    return provider, clean_url, models
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
            logger.debug(f"{provider} probe failed: {e}")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error probing {provider}: {e}")
            continue

    logger.warning("No active local LLM provider discovered. Falling back to simulated/mock provider.")
    return "simulated", "http://localhost:8000/mock/v1", ["mock-gpt-4", "mock-llama-3"]
