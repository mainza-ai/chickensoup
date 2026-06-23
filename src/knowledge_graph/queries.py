import logging
from typing import Dict, List, Any
from neo4j import Driver
from src.cache import cache_decorator

logger = logging.getLogger("chickensoup.neo4j.queries")

@cache_decorator(prefix="neo4j", ttl=300)
def get_entity_neighborhood(driver: Driver, entity_name: str) -> Dict[str, Any]:
    """
    Retrieves an entity and all its directly connected neighbors and relationships.
    """
    query = """
    MATCH (n:Entity)
    WHERE toLower(n.name) = toLower($name)
       OR replace(toLower(n.name), ' ', '-') = replace(toLower($name), ' ', '-')
       OR replace(toLower(n.name), '-', ' ') = replace(toLower($name), '-', ' ')
       OR replace(toLower(n.name), ' ', '-') CONTAINS replace(toLower($name), ' ', '-')
       OR replace(toLower($name), ' ', '-') CONTAINS replace(toLower(n.name), ' ', '-')
    WITH n LIMIT 1
    OPTIONAL MATCH (n)-[r]-(m:Entity)
    RETURN n, collect(r) as relationships, collect(m) as neighbors
    """
    
    with driver.session() as session:
        result = session.run(query, name=entity_name)
        record = result.single()
        if not record:
            return {"entity": None, "connections": []}
        
        entity_node = record["n"]
        rels = record["relationships"]
        neighbors = record["neighbors"]
        
        connections = []
        for r, m in zip(rels, neighbors):
            connections.append({
                "relationship_type": r.type,
                "relationship_properties": dict(r),
                "neighbor_name": m.get("name"),
                "neighbor_labels": list(m.labels),
                "neighbor_properties": dict(m)
            })
            
        return {
            "entity": {
                "name": entity_node.get("name"),
                "labels": list(entity_node.labels),
                "properties": dict(entity_node)
            },
            "connections": connections
        }

@cache_decorator(prefix="neo4j", ttl=300)
def search_entities(driver: Driver, search_term: str) -> List[Dict[str, Any]]:
    """
    Performs a fuzzy search on entity names.
    """
    query = """
    MATCH (n:Entity)
    WHERE n.name CONTAINS $term OR n.content_preview CONTAINS $term
    RETURN n LIMIT 15
    """
    results = []
    with driver.session() as session:
      res = session.run(query, term=search_term)
      for record in res:
        node = record["n"]
        results.append({
          "name": node.get("name"),
          "labels": list(node.labels),
          "confidence": node.get("confidence", 1.0),
          "preview": node.get("content_preview", "")
        })
    return results

@cache_decorator(prefix="neo4j", ttl=300)
def get_evidence_by_entity(driver: Driver, entity_name: str) -> List[str]:
    """
    Retrieves sources/citations associated with an entity.
    """
    query = """
    MATCH (n:Entity {name: $name})
    RETURN n.sources as sources
    """
    with driver.session() as session:
        result = session.run(query, name=entity_name)
        record = result.single()
        if record and record["sources"]:
            return list(record["sources"])
    return []
