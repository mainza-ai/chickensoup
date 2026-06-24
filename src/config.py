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

    QUANTUM_SIMULATION_BACKEND: str = "numpy"
    IBM_API_TOKEN: str = ""
    DWAVE_API_TOKEN: str = ""
    IONQ_API_TOKEN: str = ""
    QUANTUM_HARDWARE_ENABLED: bool = False

    @property
    def fallback_chain_list(self) -> List[str]:
        return [provider.strip() for provider in self.LLM_FALLBACK_CHAIN.split(",") if provider.strip()]

settings = Settings()
