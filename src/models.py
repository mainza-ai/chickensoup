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

class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Raw text content to analyze for wiki page extraction")
    filename: Optional[str] = Field(None, description="Original filename for source attribution")

class SuggestedPageModel(BaseModel):
    title: str
    page_type: str = Field(..., pattern=r"^(entities|concepts|projects)$")
    tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    summary: str = ""
    body: str = ""
    related: List[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)

class AnalyzeResponse(BaseModel):
    success: bool
    suggested_pages: List[SuggestedPageModel] = Field(default_factory=list)
    confidence: float
    raw_text_preview: str = ""

class FileIngestResponse(BaseModel):
    success: bool
    pages_created: List[str] = Field(default_factory=list)
    pages_updated: List[str] = Field(default_factory=list)
    total_pages: int = 0
    nodes_created: int = 0
    relationships_created: int = 0

class FolderIngestResponse(BaseModel):
    success: bool
    total_files: int = 0
    total_pages_created: int = 0
    total_pages_updated: int = 0
    total_nodes_created: int = 0
    total_relationships_created: int = 0
    file_results: List[FileIngestResponse] = Field(default_factory=list)
    failed_files: List[Dict[str, str]] = Field(default_factory=list)

class WikiClearResponse(BaseModel):
    success: bool
    dry_run: bool = True
    preserved_count: int = 0
    deleted_count: int = 0
    protected_added_count: int = 0
    preserved_slugs: List[str] = Field(default_factory=list)
    deleted_slugs: List[str] = Field(default_factory=list)

class WikiExportResponse(BaseModel):
    success: bool
    filepath: str = ""
    size_kb: float = 0.0
    page_count: int = 0

class WikiImportResponse(BaseModel):
    success: bool
    restored_count: int = 0

class WikiPageListItem(BaseModel):
    slug: str
    title: str
    page_type: str
    tags: List[str] = Field(default_factory=list)
    created: str = ""
    updated: str = ""
    protected: bool = False

class WikiPageListResponse(BaseModel):
    success: bool
    pages: List[WikiPageListItem] = Field(default_factory=list)
    total: int = 0

class WikiPageDetailResponse(BaseModel):
    success: bool
    slug: str = ""
    title: str = ""
    page_type: str = ""
    tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)
    body: str = ""
    created: str = ""
    updated: str = ""
    protected: bool = False

class WikiDeleteResponse(BaseModel):
    success: bool
    slug: str = ""
    page_type: str = ""
    title: str = ""
    neo4j_cleaned: bool = False
    cross_refs_cleaned: int = 0

class ConversationMetaResponse(BaseModel):
    id: str
    message_count: int = 0
    last_activity: Optional[str] = None
    ingested: bool = False
    ingested_at: Optional[str] = None
    pages_created: List[str] = Field(default_factory=list)

class ChatIngestStatusResponse(BaseModel):
    enabled: bool
    last_run: Optional[str] = None
    conversations_checked: int = 0
    conversations_ingested: int = 0
    pages_created: int = 0
    pages_updated: int = 0

class SetUserNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="New display name for the user wiki entity")

class SetUserNameResponse(BaseModel):
    success: bool
    previous_name: str
    current_name: str
    slug: str
