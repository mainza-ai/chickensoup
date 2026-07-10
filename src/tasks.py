import os
import logging
from typing import Dict, Any, List
from celery import Celery
from src.config import settings

logger = logging.getLogger("chickensoup.tasks")

# Initialize Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("chickensoup", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.async_ingest_page")
def async_ingest_page(title: str, content: str, tags: List[str], sources: List[str]) -> Dict[str, Any]:
    logger.info(f"Asynchronously ingesting wiki page: {title}")
    from src.knowledge_graph.ingest import ingest_wiki_page
    from src.knowledge_graph.connection import neo4j_conn
    
    driver = neo4j_conn.get_driver()
    if not driver:
        driver = neo4j_conn.connect()
        
    try:
        result = ingest_wiki_page(driver, title, content, tags, sources)
        return {
            "success": True,
            "title": title,
            "nodes_created": result.get("nodes_created", 0),
            "relationships_created": result.get("relationships_created", 0),
            "confidence_score": result.get("confidence_score", 1.0)
        }
    except Exception as e:
        logger.error(f"Error in async ingestion task for {title}: {e}")
        return {
            "success": False,
            "error": str(e),
            "title": title
        }

@celery_app.task(name="tasks.async_navigate")
def async_navigate(origin: str, destination: str, target_year: int, energy_level: float) -> Dict[str, Any]:
    logger.info(f"Asynchronously calculating spacetime trajectory from {origin} to {destination}")
    from src.spacetime_engine.tensor import FieldGeometryTensor
    from src.quantum_scheduler import QuantumJobScheduler
    
    scheduler = QuantumJobScheduler()
    geometry = FieldGeometryTensor(
        warp_factor=energy_level * 1.2,
        metric_tensor=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        extrinsic_curvature=[[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]]
    )
    
    try:
        job_info = scheduler.submit_job(settings.QUANTUM_SIMULATION_BACKEND, geometry)
        
        # Simulate quick processing or let it check status
        import time
        time.sleep(1.0)
        
        completed_job = scheduler.get_job_status(job_info["job_id"])
        
        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "path": [origin, f"Warp-Node-{target_year}", destination],
            "warp_factor": completed_job.get("result", {}).get("measured_warp_factor", energy_level * 1.2),
            "divergence_risk": 0.05
        }
    except Exception as e:
        logger.error(f"Error in async navigation task: {e}")
        return {
            "success": False,
            "error": str(e)
        }
