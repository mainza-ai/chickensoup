from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query string to evaluate (e.g. Vatican UFO recovery, 1937)")
    structured: bool = Field(False, description="Whether to return a structured JSON response instead of free text")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for multi-turn context")

class QueryResponse(BaseModel):
    query: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    inferred_events: List[Dict[str, Any]] = Field(default_factory=list)
    inferred_entities: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up queries")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Previous turns in this conversation")

class NavigateRequest(BaseModel):
    origin: str = Field(..., description="Origin location or epoch (e.g. Earth-2026)")
    destination: str = Field(..., description="Destination location or epoch (e.g. Earth-1947)")
    target_year: int = Field(..., description="Target year to navigate to")
    energy_level: float = Field(1.0, description="Field energy manipulation scale")

class NavigateResponse(BaseModel):
    success: bool
    path: List[str] = Field(default_factory=list, description="Computed path steps through spacetime")
    warp_factor: float = Field(..., description="Calculated spacetime distortion factor")
    divergence_risk: float = Field(..., description="Probability of timeline divergence or splitting")
    geometry_tensor: Dict[str, Any] = Field(..., description="Serialized ADM 3+1 FieldGeometryTensor state")

class IngestRequest(BaseModel):
    title: str = Field(..., description="Title of the wiki page/source")
    content: str = Field(..., description="Full text/markdown content to parse")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the source")
    sources: List[str] = Field(default_factory=list, description="Document sources cited")

class IngestResponse(BaseModel):
    success: bool
    nodes_created: int
    relationships_created: int
    confidence_score: float

class StatusResponse(BaseModel):
    status: str
    llm_provider: str
    llm_connected: bool
    neo4j_connected: bool
    redis_connected: bool
    quantum_backend: str

class ModelsResponse(BaseModel):
    provider: str
    models: List[str]

class LLMProviderStatus(BaseModel):
    available: bool = False
    models: List[str] = []

class ConfigRequest(BaseModel):
    quantum_backend: str
    ibm_api_token: Optional[str] = None
    dwave_api_token: Optional[str] = None
    ionq_api_token: Optional[str] = None
    quantum_hardware_enabled: bool = False
    llm_active_provider: Optional[str] = None
    llm_active_model: Optional[str] = None

class ConfigResponse(BaseModel):
    success: bool
    quantum_backend: str
    quantum_hardware_enabled: bool
    ibm_api_token_set: bool
    dwave_api_token_set: bool
    ionq_api_token_set: bool
    llm_active_provider: str
    llm_active_model: str
    llm_available_models: List[str]
    llm_providers: Dict[str, LLMProviderStatus] = {}

class LLMConfigRequest(BaseModel):
    llm_active_provider: Optional[str] = None
    llm_active_model: Optional[str] = None

class LLMConfigResponse(BaseModel):
    success: bool
    llm_active_provider: str
    llm_active_model: str
    llm_available_models: List[str]
    llm_providers: Dict[str, LLMProviderStatus] = {}

class LLMProbeRequest(BaseModel):
    provider_name: str = Field(..., description="Provider to probe: omlx, ollama, lmstudio")

class LLMProbeResponse(BaseModel):
    provider: str
    available: bool = False
    models: List[str] = Field(default_factory=list)
