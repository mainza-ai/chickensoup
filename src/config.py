import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PORT: int = 8000
    HOST: str = "0.0.0.0"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "chickensoup_password"

    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_FALLBACK_CHAIN: str = "omlx,ollama,lmstudio"
    OMLX_API_URL: str = "http://127.0.0.1:9000/v1"
    OLLAMA_API_URL: str = "http://localhost:11434/v1"
    LMSTUDIO_API_URL: str = "http://localhost:1234/v1"

    # Override auto-discovered provider/model (empty = auto-select)
    LLM_ACTIVE_PROVIDER: str = ""
    LLM_ACTIVE_MODEL: str = ""

    QUANTUM_SIMULATION_BACKEND: str = "numpy"
    IBM_API_TOKEN: str = ""
    DWAVE_API_TOKEN: str = ""
    IONQ_API_TOKEN: str = ""
    QUANTUM_HARDWARE_ENABLED: bool = False

    WIKI_AUTO_CREATE: bool = True
    WIKI_MIN_CONFIDENCE: float = 0.5
    WIKI_DATA_DIR: str = "wiki"

    # Wiki backup settings
    WIKI_BACKUP_ENABLED: bool = True
    WIKI_BACKUP_DIR: str = "backups"
    WIKI_BACKUP_RETENTION_DAYS: int = 30
    WIKI_AUTO_COMMIT: bool = False

    # Chat-to-wiki periodic conversion
    CHAT_WIKI_CONVERSION_ENABLED: bool = False
    CHAT_WIKI_MIN_CONVERSATION_LENGTH: int = 10
    CHAT_WIKI_CHECK_INTERVAL_SECONDS: int = 300
    CHAT_WIKI_IDLE_TIMEOUT_MINUTES: int = 30
    CHAT_WIKI_USER_ENTITY_NAME: str = "Primary Researcher"

    # Orchestrator graph timeout (seconds)
    ORCHESTRATOR_TIMEOUT_SECONDS: int = 120

    @property
    def fallback_chain_list(self) -> List[str]:
        return [provider.strip() for provider in self.LLM_FALLBACK_CHAIN.split(",") if provider.strip()]

settings = Settings()
