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

    # Cloud LLM providers
    NVIDIA_API_KEY: str = ""
    NVIDIA_API_URL: str = "https://integrate.api.nvidia.com/v1"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1"
    CUSTOM_LLM_API_KEY: str = ""
    CUSTOM_LLM_API_URL: str = ""
    CUSTOM_LLM_MODELS: str = ""

    # LLM provider type: "local" (auto-discover fallback chain) or "cloud" (use specified provider)
    LLM_PROVIDER_TYPE: str = "local"

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

    # Neo4j database backup settings
    NEO4J_BACKUP_ENABLED: bool = True
    NEO4J_BACKUP_DIR: str = "backups/neo4j"
    NEO4J_BACKUP_RETENTION_DAYS: int = 30
    NEO4J_BACKUP_INTERVAL_HOURS: int = 24
    NEO4J_URI_HOST_DATA: str = "/var/lib/docker/volumes/chickensoup_neo4j_data/_data"
    NEO4J_CONTAINER_NAME: str = "chickensoup-neo4j"
    NEO4J_DATA_VOLUME: str = "chickensoup_neo4j_data"

    # Chat-to-wiki periodic conversion
    CHAT_WIKI_CONVERSION_ENABLED: bool = False
    CHAT_WIKI_MIN_CONVERSATION_LENGTH: int = 10
    CHAT_WIKI_CHECK_INTERVAL_SECONDS: int = 300
    CHAT_WIKI_IDLE_TIMEOUT_MINUTES: int = 30
    CHAT_WIKI_USER_ENTITY_NAME: str = "Primary Researcher"

    # Security
    API_KEY: str = ""  # Empty = dev mode (no auth required)
    CORS_ORIGINS: str = "http://127.0.0.1:8000,http://localhost:8000"

    # Orchestrator graph timeout (seconds)
    ORCHESTRATOR_TIMEOUT_SECONDS: int = 120

    # Concurrency and rate limiting
    MAX_CONCURRENT_LLM_REQUESTS: int = 4  # 2 high priority + 2 low priority
    REQUEST_RATE_LIMIT_PER_MINUTE: int = 20
    REQUEST_RATE_LIMIT_BURST: int = 5
    REQUEST_MAX_BODY_BYTES: int = 1_048_576  # 1 MB default
    RATE_LIMITING_ENABLED: bool = True

    # Request ID and observability
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Checkpointer backend
    CHECKPOINT_BACKEND: str = "redis"

    # LLM circuit breaker
    LLM_CIRCUIT_BREAKER_THRESHOLD: int = 5
    LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 120  # local LLM restart takes time

    # LLM client (shared across all call sites)
    # Timeout is adjusted dynamically in llm_client.py based on provider type:
    # cloud providers (NVIDIA, OpenRouter) → 30s, local (omlx/ollama/lmstudio) → 120s
    LLM_CLIENT_TIMEOUT: float = 30.0
    LLM_CLIENT_CLOUD_TIMEOUT: float = 30.0
    LLM_CLIENT_LOCAL_TIMEOUT: float = 120.0
    LLM_CLIENT_MAX_TOKENS: int = 2048
    LLM_CLIENT_HIGH_PRIORITY_CONCURRENCY: int = 2
    LLM_CLIENT_LOW_PRIORITY_CONCURRENCY: int = 2

    # LLM edge classification (knowledge graph ingest) — DEPRECATED
    # The LLM path has been removed (Phase 3). Edge classification is now
    # handled exclusively by heuristics. These settings remain for backward
    # compatibility but are no longer used by any code path.
    LLM_EDGE_CLASSIFICATION_TIMEOUT: int = 0
    LLM_EDGE_CLASSIFICATION_MAX_RETRIES: int = 0

    # Living Almanac / last30days integration
    LAST30DAYS_ENABLED: bool = False
    LAST30DAYS_BINARY_PATH: str = ""
    LAST30DAYS_MONTHLY_BUDGET_USD: float = 20.0
    LAST30DAYS_COST_PER_PULL_USD: float = 0.50
    FREE_TIER_REQUESTS_PER_HOUR: int = 60
    FREE_TIER_ENABLED: bool = True
    IDLE_THRESHOLD_MINUTES: int = 5
    LAST30DAYS_PULSE_TIMEOUT_SECONDS: int = 300

    # Wiki reconciliation at startup: ingests existing pages into Neo4j/queue.
    # Disable in tests to avoid background threads interfering with mock state.
    WIKI_RECONCILE_ON_STARTUP: bool = True
    LAST30DAYS_MAX_CLAIMS_PER_PULSE: int = 50

    LAST30DAYS_PULSE_ENABLED: bool = False

    CLAIM_WAVEFUNCTION_SOCIAL_TRACTION_WEIGHT: float = 0.15
    SOCIAL_TRACTION_HALF_LIFE_DAYS: float = 7.0
    SOCIAL_TRACTION_DECAY_ENABLED: bool = True

    ALMANAC_GENERATION_INTERVAL_HOURS: int = 24
    ALMANAC_DRY_RUN_DEFAULT: bool = True
    ALMANAC_MIN_ENTITIES: int = 2

    BUDGET_REDIS_KEY_PREFIX: str = "budget"
    BUDGET_HOLD_THRESHOLD_REMAINING: float = 2.0  # multiples of cost_per_pull

    # Quantum credibility
    WAVEFUNCTION_SCORING_VERSION: str = "v1-wavefunction"
    DIVERGENCE_SPIKE_THRESHOLD: float = 0.7

    @property
    def fallback_chain_list(self) -> List[str]:
        return [provider.strip() for provider in self.LLM_FALLBACK_CHAIN.split(",") if provider.strip()]

settings = Settings()
