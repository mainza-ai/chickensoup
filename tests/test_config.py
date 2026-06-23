import os
from unittest.mock import patch
from src.config import Settings

def test_settings_default_values():
    settings = Settings()
    assert settings.PORT == 8000
    assert settings.HOST == "0.0.0.0"
    assert settings.NEO4J_URI == "bolt://localhost:7687"
    assert "omlx" in settings.fallback_chain_list

def test_fallback_chain_list_parsing():
    settings = Settings(LLM_FALLBACK_CHAIN="omlx, lmstudio")
    assert settings.fallback_chain_list == ["omlx", "lmstudio"]

    settings_empty = Settings(LLM_FALLBACK_CHAIN="")
    assert settings_empty.fallback_chain_list == []

def test_env_override():
    with patch.dict(os.environ, {"PORT": "9000", "LLM_FALLBACK_CHAIN": "ollama"}):
        settings = Settings()
        assert settings.PORT == 9000
        assert settings.fallback_chain_list == ["ollama"]
