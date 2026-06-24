import json
import urllib.error
from unittest.mock import patch, MagicMock
from src.discovery import refresh_discovery, get_discovered, get_active_model, get_active_provider

def _clear_discovery_cache():
    """Reset the module-level cache for test isolation."""
    import src.discovery as d
    d._discovered_provider = None
    d._discovered_base_url = None
    d._discovered_models = []

def test_discover_active_provider_fallback():
    _clear_discovery_cache()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        provider, url, models = refresh_discovery()
        assert provider == "simulated"
        assert "mock-gpt-4" in models

def test_discover_active_provider_success_omlx():
    _clear_discovery_cache()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "data": [{"id": "omlx-model-1"}, {"id": "omlx-model-2"}]
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response

        provider, url, models = refresh_discovery()
        assert provider == "omlx"
        assert url == "http://127.0.0.1:9000/v1"
        assert models == ["omlx-model-1", "omlx-model-2"]

def test_discover_active_provider_success_ollama_after_omlx_fail():
    _clear_discovery_cache()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps([
        {"id": "ollama-llama3"},
        {"name": "ollama-mistral"}
    ]).encode("utf-8")

    fail_effect = urllib.error.URLError("Connection refused")

    def urlopen_side_effect(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        if "9000" in url:
            raise fail_effect
        cm = MagicMock()
        cm.__enter__.return_value = mock_response
        return cm

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        provider, url, models = refresh_discovery()
        assert provider == "ollama"
        assert url == "http://localhost:11434/v1"
        assert "ollama-llama3" in models

def test_get_discovered_caching():
    _clear_discovery_cache()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "data": [{"id": "cached-model"}]
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        provider, url, models = get_discovered(depth="fresh")
        assert models == ["cached-model"]

        # Second call with default "cached" should not re-probe
        provider, url, models = get_discovered()
        assert models == ["cached-model"]
        assert mock_urlopen.call_count == 1

def test_get_active_model_fallback():
    _clear_discovery_cache()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        refresh_discovery()
        model = get_active_model()
        # After fallback, first model is "mock-gpt-4"
        assert model == "mock-gpt-4"
