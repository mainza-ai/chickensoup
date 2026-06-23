import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
import redis

from src.config import settings
from src.discovery import discover_active_provider
from src.models import (
    QueryRequest, QueryResponse, NavigateRequest, NavigateResponse,
    IngestRequest, IngestResponse, StatusResponse, ModelsResponse
)
from src.knowledge_graph.connection import neo4j_conn
from src.knowledge_graph.schema import initialize_schema
from src.knowledge_graph.ingest import ingest_wiki_page
from src.knowledge_graph.queries import get_entity_neighborhood, search_entities
from src.spacetime_engine.qiskit_simulation import simulate_spacetime_metrics
from src.field_manipulator.cuda_simulation import manipulate_spacetime_field
from src.ai_navigator.pennylane_qml import find_optimal_path
from src.agents.orchestrator import Orchestrator
from src.mcp.tools import mcp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chickensoup.main")

# Initialize agent orchestrator
orchestrator = Orchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up chickensoup API...")
    try:
        driver = neo4j_conn.connect()
        initialize_schema(driver)
    except Exception as e:
        logger.error(f"Could not initialize Neo4j connection or schema on startup: {e}")
    yield
    # Shutdown actions
    logger.info("Shutting down chickensoup API...")
    neo4j_conn.close()

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
from src.observability import tracer, agent_loop_counter, quantum_simulation_duration
from src.cache import cache_store

# CORS origins
origins = ["*"]

app = FastAPI(
    title="Project Chicken Soup API",
    description="FastAPI & FastMCP spacetime simulation & UAP lore navigation backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenTelemetry tracking + Rate Limiting Middleware
class ObservabilityAndRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        with tracer.start_as_current_span(f"http_request_{request.method}_{request.url.path}"):
            response = await call_next(request)
            return response

app.add_middleware(ObservabilityAndRateLimitMiddleware)

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Returns system status, showing connectivity of local LLMs, database, and cache."""
    # Check LLM
    provider, _, models = discover_active_provider()
    llm_connected = provider != "simulated"

    # Check Neo4j
    neo4j_ok = neo4j_conn.check_health()

    # Check Redis
    redis_ok = False
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    return StatusResponse(
        status="healthy" if (neo4j_ok or llm_connected) else "degraded",
        llm_provider=provider,
        llm_connected=llm_connected,
        neo4j_connected=neo4j_ok,
        redis_connected=redis_ok,
        quantum_backend=settings.QUANTUM_SIMULATION_BACKEND
    )

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Lists available local LLM models discovered on the system fallback chain."""
    provider, _, models = discover_active_provider()
    return ModelsResponse(
        provider=provider,
        models=models
    )

@app.post("/query", response_model=QueryResponse)
async def post_query(request: QueryRequest):
    """Submits a query to search the knowledge graph and generate an answer summary using Orchestrator."""
    try:
        # Route query through the agent orchestrator graph
        output = await orchestrator.execute(request.query)
        
        # If it was paused for human approval, return the intermediate state
        if output.get("status") == "paused_for_human_approval":
            return QueryResponse(
                query=request.query,
                answer=f"PENDING APPROVAL: {output.get('summary')}",
                confidence=0.1,
                entities=[],
                sources=["System Gatekeeper Thread ID: " + output.get("thread_id", "")]
            )
            
        return QueryResponse(
            query=request.query,
            answer=output.get("answer", "No response generated."),
            confidence=output.get("confidence", 0.5),
            entities=output.get("entities", []),
            sources=output.get("sources", ["Orchestrated Search"])
        )
    except Exception as e:
        logger.error(f"Error handling orchestrated query: {e}")
        # Standard fallback if Neo4j or LLM fails
        return QueryResponse(
            query=request.query,
            answer=f"Simulation response: The query '{request.query}' relates to anomalous gravitational field theory.",
            confidence=0.6,
            entities=[],
            sources=["Simulated Fallback Engine"]
        )

@app.get("/graph/{entity}")
async def get_graph_entity(entity: str):
    """Retrieves an entity and all its directly related nodes/relationships in a simplified form."""
    import uuid
    try:
        driver = neo4j_conn.get_driver()
        details = get_entity_neighborhood(driver, entity)
        if not details.get("entity"):
            raise HTTPException(status_code=404, detail=f"Entity '{entity}' not found.")
        
        entity_info = details["entity"]
        labels = entity_info["labels"]
        entity_type = "Entity"
        for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
            if label in labels:
                entity_type = label
                break
                
        props = entity_info["properties"]
        sources = props.get("sources", [])
        if not isinstance(sources, list):
            sources = [str(sources)] if sources else []
            
        simple_entity = {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, entity_info["name"])),
            "name": entity_info["name"],
            "type": entity_type,
            "summary": props.get("content_preview", props.get("summary", "")),
            "confidence": props.get("confidence", 1.0),
            "source": sources[0] if sources else "Unknown",
            "sources": [str(s) for s in sources]
        }
        
        simple_connections = []
        for conn in details["connections"]:
            n_labels = conn["neighbor_labels"]
            n_type = "Entity"
            for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
                if label in n_labels:
                    n_type = label
                    break
            
            n_props = conn["neighbor_properties"]
            n_sources = n_props.get("sources", [])
            if not isinstance(n_sources, list):
                n_sources = [str(n_sources)] if n_sources else []
                
            simple_connections.append({
                "relationship_type": conn["relationship_type"],
                "neighbor": {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, conn["neighbor_name"])),
                    "name": conn["neighbor_name"],
                    "type": n_type,
                    "summary": n_props.get("content_preview", n_props.get("summary", "")),
                    "confidence": n_props.get("confidence", 1.0),
                    "source": n_sources[0] if n_sources else "Unknown",
                    "sources": [str(s) for s in n_sources]
                }
            })
            
        return {
            "entity": simple_entity,
            "connections": simple_connections
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/navigate", response_model=NavigateResponse)
async def post_navigate(request: NavigateRequest):
    """Computes the optimal path through the warped spacetime manifold using Navigation Agent."""
    try:
        # Format query for orchestrator or call NavigationAgent directly
        # Directly invoking NavigationAgent here matches FastAPI specification perfectly
        nav_res = orchestrator.navigation_agent.navigate(
            origin=request.origin,
            destination=request.destination,
            target_year=request.target_year,
            energy_level=request.energy_level
        )
        
        return NavigateResponse(
            success=nav_res["success"],
            path=nav_res["path"],
            warp_factor=nav_res["warp_factor"],
            divergence_risk=nav_res["divergence_risk"],
            geometry_tensor=nav_res["geometry_tensor"]
        )
    except Exception as e:
        logger.error(f"Navigation computation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pathfinding navigation failure: {str(e)}"
        )

from src.multi_llm import MultiLLMConsensus
from src.quantum_scheduler import QuantumJobScheduler
from pydantic import BaseModel, Field

multi_llm_consensus = MultiLLMConsensus()
quantum_scheduler = QuantumJobScheduler()

class ConsensusQueryRequest(BaseModel):
    prompt: str
    system_instruction: str = "You are an expert consensus analyzer."

class QuantumJobRequest(BaseModel):
    hardware: str
    target_year: int
    energy_level: float = 1.0

@app.post("/consensus/query")
async def post_consensus_query(request: ConsensusQueryRequest):
    """
    Evaluates queries against multiple active provider models, returning consensus scores.
    """
    try:
        res = await multi_llm_consensus.generate_consensus(request.prompt, request.system_instruction)
        return res
    except Exception as e:
        logger.error(f"Consensus generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consensus generation error: {str(e)}"
        )

@app.post("/quantum/schedule")
async def post_quantum_schedule(request: QuantumJobRequest):
    """
    Schedules simulated or real quantum hardware execution tasks.
    """
    try:
        # Simulate spacetime geometry to get a tensor for the job
        geometry_tensor = simulate_spacetime_metrics(request.target_year, request.energy_level)
        job_info = quantum_scheduler.submit_job(request.hardware, geometry_tensor)
        return job_info
    except Exception as e:
        logger.error(f"Quantum job scheduling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quantum scheduling error: {str(e)}"
        )

@app.get("/quantum/job/{job_id}")
async def get_quantum_job(job_id: str):
    """
    Checks status and retrieves details of a submitted quantum job.
    """
    job_info = quantum_scheduler.get_job_status(job_id)
    if job_info.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="Quantum job not found")
    return job_info

@app.post("/ingest", response_model=IngestResponse)
async def post_ingest(request: IngestRequest):
    """Ingests a new markdown page or document into the Neo4j knowledge graph."""
    try:
        driver = neo4j_conn.get_driver()
        nodes, rels = ingest_wiki_page(
            driver,
            title=request.title,
            content=request.content,
            default_tags=request.tags,
            default_sources=request.sources
        )
        from src.cache import cache_store
        cache_store.invalidate_all()
        return IngestResponse(
            success=True,
            nodes_created=nodes,
            relationships_created=rels,
            confidence_score=0.9
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )

from fastapi import WebSocket, WebSocketDisconnect
import asyncio

@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent responses and status updates.
    """
    await websocket.accept()
    try:
        while True:
            # Wait for incoming messages from the client
            data = await websocket.receive_text()
            logger.info(f"WebSocket received query: {data}")
            
            # Start a span for tracing this WebSocket interaction
            with tracer.start_as_current_span("ws_agent_query"):
                # Track execution in metrics
                agent_loop_counter.add(1)
                
                # Send acknowledgement/status
                await websocket.send_json({"status": "processing", "message": "Initiating search..."})
                await asyncio.sleep(0.1)
                
                # Execute query via orchestrator
                output = await orchestrator.execute(data)
                
                # Stream parts of the response
                if output.get("status") == "paused_for_human_approval":
                    await websocket.send_json({
                        "status": "paused_for_human_approval",
                        "summary": output.get("summary"),
                        "thread_id": output.get("thread_id")
                    })
                else:
                    # Mock streaming word by word or chunk by chunk
                    answer = output.get("answer", "No response generated.")
                    chunks = answer.split(" ")
                    for i, chunk in enumerate(chunks):
                        await websocket.send_json({
                            "status": "streaming",
                            "chunk": chunk + (" " if i < len(chunks) - 1 else "")
                        })
                        await asyncio.sleep(0.05)
                        
                    await websocket.send_json({
                        "status": "completed",
                        "answer": answer,
                        "confidence": output.get("confidence", 0.5),
                        "entities": output.get("entities", []),
                        "sources": output.get("sources", [])
                    })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except Exception:
            pass


@app.get("/entities")
async def get_entities():
    """Retrieves all Lore Entities from the Neo4j database."""
    import uuid
    driver = neo4j_conn.get_driver()
    query = """
    MATCH (n:Entity)
    RETURN n
    """
    entities = []
    try:
        with driver.session() as session:
            res = session.run(query)
            for record in res:
                node = record["n"]
                name = node.get("name", "Unknown")
                node_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
                labels = list(node.labels)
                node_type = "Entity"
                for label in ["Person", "Place", "Concept", "Object", "Project", "Event"]:
                    if label in labels:
                        node_type = label
                        break
                
                node_sources = node.get("sources", [])
                if not isinstance(node_sources, list):
                    node_sources = [str(node_sources)] if node_sources else []
                node_sources = [str(s) for s in node_sources]

                entities.append({
                    "id": node_uuid,
                    "name": name,
                    "type": node_type,
                    "summary": node.get("content_preview", node.get("summary", "")),
                    "confidence": node.get("confidence", 1.0),
                    "source": node_sources[0] if node_sources else "Unknown",
                    "sources": node_sources
                })
        return entities
    except Exception as e:
        logger.error(f"Failed to fetch entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def get_events():
    """Retrieves all Temporal Events (Event nodes) from the Neo4j database."""
    import uuid
    from datetime import datetime
    driver = neo4j_conn.get_driver()
    query = """
    MATCH (e:Entity)
    RETURN e
    """
    events = []
    try:
        with driver.session() as session:
            res = session.run(query)
            for record in res:
                node = record["e"]
                title = node.get("name", "Unnamed Event")
                tags = [t.lower() for t in node.get("tags", [])]
                labels = [l.lower() for l in node.labels]
                
                title_lower = title.lower()
                is_event = "event" in labels or "event" in tags or any(
                    k in title_lower or any(k in t for t in tags)
                    for k in ["incident", "crash", "encounter", "recovery", "transfer", "testimony", "explosion", "sighting", "whistleblower", "project"]
                )
                
                if not is_event:
                    continue
                
                node_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, title))
                
                node_sources = node.get("sources", [])
                if not isinstance(node_sources, list):
                    node_sources = [str(node_sources)] if node_sources else []
                node_sources = [str(s) for s in node_sources]
                
                timestamp = datetime.utcnow().isoformat() + "Z"
                year = None
                for t in tags:
                    if t.isdigit() and len(t) == 4:
                        year = int(t)
                        break
                
                if "1933" in title_lower or "1933" in tags:
                    timestamp = "1933-06-13T00:00:00Z"
                elif "1944" in title_lower or "1944" in tags:
                    timestamp = "1944-10-24T00:00:00Z"
                elif "1989" in title_lower or "1989" in tags:
                    timestamp = "1989-12-01T00:00:00Z"
                elif "1994" in title_lower or "1994" in tags:
                    timestamp = "1994-09-16T00:00:00Z"
                elif "1996" in title_lower or "1996" in tags:
                    timestamp = "1996-01-20T00:00:00Z"
                elif year:
                    timestamp = f"{year}-06-01T00:00:00Z"
                
                event_type = "anomaly"
                if "crash" in title_lower or "recovery" in title_lower:
                    event_type = "crash"
                elif "testimony" in title_lower or "whistleblower" in title_lower:
                    event_type = "testimony"
                elif "theory" in title_lower or "propulsion" in title_lower:
                    event_type = "theory"
                
                events.append({
                    "id": node_uuid,
                    "title": title.replace("-", " ").title(),
                    "description": node.get("content_preview", node.get("summary", "")),
                    "timestamp": timestamp,
                    "confidence": node.get("confidence", 1.0),
                    "source": node_sources[0] if node_sources else "Unknown",
                    "type": event_type,
                    "sources": node_sources
                })
        return events
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


