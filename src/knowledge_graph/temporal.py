import logging
from typing import Optional
from neo4j import Driver
from src.cache import cache_decorator

logger = logging.getLogger("chickensoup.neo4j.temporal")


@cache_decorator(prefix="temporal", ttl=120)
def get_temporal_events(driver: Driver, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Query Event nodes with optional date range filtering."""
    conditions = ["n.date IS NOT NULL"]
    params: dict = {}
    if start_date:
        conditions.append("n.date >= $start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("n.date <= $end_date")
        params["end_date"] = end_date

    where_clause = " AND ".join(conditions)
    query = f"""
    MATCH (n:Event)
    WHERE {where_clause}
    RETURN n.name AS name,
           n.display_name AS display_name,
           n.date AS date,
           n.tags AS tags,
           n.sources AS sources,
           n.content_preview AS preview,
           n.confidence AS confidence,
           labels(n) AS labels
    ORDER BY n.date ASC
    LIMIT $limit
    """
    results = []
    with driver.session() as session:
        res = session.run(query, **params, limit=limit)
        for record in res:
            results.append({
                "name": record["name"],
                "display_name": record["display_name"],
                "date": record["date"],
                "tags": list(record["tags"]) if record["tags"] else [],
                "sources": list(record["sources"]) if record["sources"] else [],
                "preview": record["preview"],
                "confidence": record["confidence"],
                "labels": list(record["labels"]),
            })
    return results


@cache_decorator(prefix="temporal", ttl=120)
def get_entity_temporal_context(driver: Driver, entity_name: str) -> list[dict]:
    """Get events connected to a specific entity, ordered chronologically."""
    query = """
    MATCH (e:Entity {name: $name})
    OPTIONAL MATCH (e)-[r]-(n:Event)
    WHERE n.date IS NOT NULL
    RETURN n.name AS name,
           n.display_name AS display_name,
           n.date AS date,
           type(r) AS relationship,
           n.confidence AS confidence,
           n.content_preview AS preview
    ORDER BY n.date ASC
    """
    results = []
    with driver.session() as session:
        res = session.run(query, name=entity_name)
        for record in res:
            if record["name"]:
                results.append({
                    "name": record["name"],
                    "display_name": record["display_name"],
                    "date": record["date"],
                    "relationship": record["relationship"],
                    "confidence": record["confidence"],
                    "preview": record["preview"],
                })
    return results


@cache_decorator(prefix="temporal", ttl=120)
def get_timeline_range(driver: Driver) -> dict:
    """Get the earliest and latest dates across all Event nodes."""
    query = """
    MATCH (n:Event)
    WHERE n.date IS NOT NULL
    RETURN min(n.date) AS earliest, max(n.date) AS latest, count(n) AS total
    """
    with driver.session() as session:
        result = session.run(query).single()
        if result:
            return {
                "earliest": result["earliest"],
                "latest": result["latest"],
                "total": result["total"],
            }
    return {"earliest": None, "latest": None, "total": 0}
