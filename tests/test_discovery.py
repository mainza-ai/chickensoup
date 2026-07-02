import json
import urllib.error
from unittest.mock import patch, MagicMock
from src.discovery import refresh_discovery, get_discovered, get_active_model, get_active_provider, probe_provider, _probe_single
import time

def _clear_discovery_cache():
    """Reset the module-level cache for test isolation."""
    import src.discovery as d
    d._discovered_provider = None
    d._discovered_base_url = None
    d._discovered_models = []
    d._discovered_all = {}
    d._discovered_at = 0.0
    d._circuit_breakers.clear()


def test_discover_active_provider_fallback():
    _clear_discovery_cache()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")), \
         patch("time.sleep"):
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
        assert url == "http://localhost:9000/v1"
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
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "9000" in url:
            raise fail_effect
        cm = MagicMock()
        cm.__enter__.return_value = mock_response
        return cm

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect), \
         patch("time.sleep"):
        provider, url, models = refresh_discovery()
        assert provider == "ollama"
        assert url == "http://localhost:11434/v1"
        assert "ollama-llama-3" in models or "ollama-llama3" in models


def test_override_falls_through_to_chain_when_unreachable():
    """LLM_ACTIVE_PROVIDER=ollama but ollama is down → fallback to oMLX."""
    import src.config as cfg
    import src.discovery as d
    _clear_discovery_cache()

    original_override = cfg.settings.LLM_ACTIVE_PROVIDER
    cfg.settings.LLM_ACTIVE_PROVIDER = "ollama"

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "data": [{"id": "omlx-model-1"}]
    }).encode("utf-8")

    def urlopen_side_effect(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "11434" in url:
            raise urllib.error.URLError("Connection refused")
        cm = MagicMock()
        cm.__enter__.return_value = mock_response
        return cm

    try:
        with patch("urllib.request.urlopen", side_effect=urlopen_side_effect), \
             patch("time.sleep"):
            provider, url, models = refresh_discovery()
            assert provider == "omlx"
            assert "omlx-model-1" in models
    finally:
        cfg.settings.LLM_ACTIVE_PROVIDER = original_override


def test_probe_tries_multiple_model_paths():
    """404 on /v1/models → falls back to /models and succeeds."""
    _clear_discovery_cache()

    mock_200 = MagicMock()
    mock_200.status = 200
    mock_200.read.return_value = json.dumps({
        "data": [{"id": "ollama-llama3"}]
    }).encode("utf-8")

    mock_404 = MagicMock()
    mock_404.status = 404
    mock_404.read.return_value = b"{}"

    def urlopen_side_effect(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url.endswith("/v1/models"):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        cm = MagicMock()
        cm.__enter__.return_value = mock_200
        return cm

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect), \
         patch("time.sleep"):
        result = _probe_single("ollama")
        assert result["available"] is True
        assert "ollama-llama3" in result["models"]


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

        # refresh_discovery now probes all providers (3 total)
        assert mock_urlopen.call_count == 3

        # Second call with default "cached" should not re-probe
        provider, url, models = get_discovered()
        assert models == ["cached-model"]
        assert mock_urlopen.call_count == 3


def test_get_active_model_fallback():
    _clear_discovery_cache()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")), \
         patch("time.sleep"):
        refresh_discovery()
        model = get_active_model()
        # After fallback, first model is "mock-gpt-4"
        assert model == "mock-gpt-4"


def test_probe_provider_returns_error_on_failure():
    _clear_discovery_cache()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")), \
         patch("time.sleep"):
        provider, url, models, error = probe_provider("omlx")
        assert provider == "simulated"
        assert models == []
        assert error is not None
