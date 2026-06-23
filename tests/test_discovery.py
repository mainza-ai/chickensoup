import json
import urllib.error
from unittest.mock import patch, MagicMock
from src.discovery import discover_active_provider

def test_discover_active_provider_fallback():
    # Mock urllib.request.urlopen to raise URLError for all endpoints
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        provider, url, models = discover_active_provider()
        assert provider == "simulated"
        assert "mock-gpt-4" in models

def test_discover_active_provider_success_omlx():
    # Mock urllib.request.urlopen to succeed for the first provider (omlx)
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "data": [{"id": "omlx-model-1"}, {"id": "omlx-model-2"}]
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        provider, url, models = discover_active_provider()
        assert provider == "omlx"
        assert url == "http://127.0.0.1:9000/v1"
        assert models == ["omlx-model-1", "omlx-model-2"]

def test_discover_active_provider_success_ollama_after_omlx_fail():
    # Mock first call (omlx) to fail, second call (ollama) to succeed
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps([
        {"id": "ollama-llama3"},
        {"name": "ollama-mistral"}
    ]).encode("utf-8")

    fail_effect = urllib.error.URLError("Connection refused")
    
    # We create a side effect function for urlopen
    def urlopen_side_effect(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        if "9000" in url:
            raise fail_effect
        # Return context manager mock
        cm = MagicMock()
        cm.__enter__.return_value = mock_response
        return cm

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        provider, url, models = discover_active_provider()
        assert provider == "ollama"
        assert url == "http://localhost:11434/v1"
        assert "ollama-llama3" in models
