import logging
from typing import Dict, Any, List
from fastmcp import FastMCP

from src.spacetime_engine.tensor import FieldGeometryTensor
from src.spacetime_engine.qiskit_simulation import simulate_spacetime_metrics
from src.field_manipulator.cuda_simulation import manipulate_spacetime_field
from src.ai_navigator.pennylane_qml import find_optimal_path
from src.knowledge_graph.connection import neo4j_conn
from src.knowledge_graph.queries import search_entities, get_evidence_by_entity, get_entity_neighborhood

logger = logging.getLogger("chickensoup.mcp.tools")

mcp = FastMCP("chickensoup")

@mcp.tool
def simulate_spacetime(target_year: int, energy_level: float = 1.0) -> Dict[str, Any]:
    """
    Simulates spacetime warping and Closed Timelike Curves using a quantum/classical tensor circuit.
    
    Args:
        target_year: Target destination year (e.g. 1947).
        energy_level: Scaling factor for gravitational/field energy manipulation.
    """
    tensor = simulate_spacetime_metrics(target_year, energy_level)
    return tensor.model_dump()

@mcp.tool
def analyze_field(warp_factor: float, lapse: float = 1.0, frequency: float = 7.46) -> Dict[str, Any]:
    """
    Simulates the bubble stability and energy density for field manipulation.
    
    Args:
        warp_factor: The spatial distortion/stretch factor of the spacetime metric.
        lapse: The time flow rate coefficient.
        frequency: The manipulation frequency in Hz (UFO resonance is at 7.46 Hz).
    """
    dummy_tensor = FieldGeometryTensor(
        lapse=lapse,
        warp_factor=warp_factor
    )
    result = manipulate_spacetime_field(dummy_tensor, frequency)
    return result

@mcp.tool
def find_paths(origin: str, destination: str, target_year: int, energy_level: float = 1.0) -> Dict[str, Any]:
    """
    Finds the optimal path through the field manifold using Variational QML/classical optimization.
    
    Args:
        origin: The start point/epoch name (e.g., Earth-2026).
        destination: The end point/epoch name (e.g., Earth-1947).
        target_year: The destination year coordinate.
        energy_level: Scaling factor for space warping.
    """
    tensor = simulate_spacetime_metrics(target_year, energy_level)
    result = find_optimal_path(origin, destination, tensor)
    return result

@mcp.tool
def query_graph(search_term: str) -> List[Dict[str, Any]]:
    """
    Queries the knowledge graph for matching entities or concepts based on a fuzzy search.
    
    Args:
        search_term: Term to search for (e.g. 'Vatican', 'Tesla').
    """
    try:
        driver = neo4j_conn.get_driver()
        return search_entities(driver, search_term)
    except Exception as e:
        logger.error(f"Error querying graph: {e}")
        return [{"error": f"Neo4j connection error: {str(e)}"}]

@mcp.tool
def get_evidence(entity_name: str) -> List[str]:
    """
    Fetches the source citations and documents backing claims about a specific entity or event.
    
    Args:
        entity_name: Name of the entity (e.g. 'Ariel School UFO Incident').
    """
    try:
        driver = neo4j_conn.get_driver()
        return get_evidence_by_entity(driver, entity_name)
    except Exception as e:
        logger.error(f"Error getting evidence: {e}")
        return [f"Error: {str(e)}"]

@mcp.tool
def explore_concept(concept_name: str) -> Dict[str, Any]:
    """
    Retrieves a concept and its surrounding web of connected elements/claims in the graph.
    
    Args:
        concept_name: The concept or node name (e.g. 'Schumann Resonance').
    """
    try:
        driver = neo4j_conn.get_driver()
        return get_entity_neighborhood(driver, concept_name)
    except Exception as e:
        logger.error(f"Error exploring concept: {e}")
        return {"error": f"Error: {str(e)}"}
