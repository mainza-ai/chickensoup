import logging
from neo4j import Driver
from src.cache import cache_store

logger = logging.getLogger("chickensoup.neo4j.temporal_causality")


def build_temporal_causality_chains(driver: Driver) -> dict:
    """Create PRECEDED_BY and CAUSED relationships between Event nodes
    based on date ordering and body content analysis.

    PRECEDED_BY: Each dated event connects to the chronologically previous event.
    CAUSED: Events in the same year or with causal keywords in their body.

    Returns counts of created relationships.
    """
    results = {"preceded_by": 0, "caused": 0, "events_processed": 0}

    events = _get_dated_events(driver)
    if len(events) < 2:
        logger.info(f"Temporal causality: only {len(events)} dated events, need at least 2")
        return results

    results["events_processed"] = len(events)

    # PRECEDED_BY: chronological chain
    preceded_created = _build_preceded_by(driver, events)
    results["preceded_by"] = preceded_created
    logger.info(f"Created {preceded_created} PRECEDED_BY relationships")

    # CAUSED: same-year events with causal keywords
    caused_created = _build_caused(driver, events)
    results["caused"] = caused_created
    logger.info(f"Created {caused_created} CAUSED relationships")

    # Invalidate caches
    try:
        cache_store.invalidate_by_pattern("cache:neo4j:*")
        cache_store.invalidate_by_pattern("cache:temporal:*")
    except Exception:
        pass

    return results


def _get_dated_events(driver: Driver) -> list[dict]:
    """Fetch all Event nodes with non-null dates, ordered chronologically."""
    query = """
    MATCH (e:Event)
    WHERE e.date IS NOT NULL
    RETURN e.name AS name, e.date AS date, e.content_preview AS preview
    ORDER BY e.date ASC
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(query)]


def _build_preceded_by(driver: Driver, events: list[dict]) -> int:
    """Create PRECEDED_BY relationships linking each event to the previous one."""
    count = 0
    with driver.session() as session:
        for i in range(1, len(events)):
            prev = events[i - 1]
            curr = events[i]
            if prev["date"] == curr["date"]:
                continue
            session.run("""
                MATCH (a:Event {name: $prev_name})
                MATCH (b:Event {name: $curr_name})
                MERGE (a)-[r:PRECEDED_BY]->(b)
                ON CREATE SET r.confidence = 0.9, r.inferred = true
            """, prev_name=prev["name"], curr_name=curr["name"])
            count += 1
    return count


def _build_caused(driver: Driver, events: list[dict]) -> int:
    """Create CAUSED relationships between events in the same year
    when body text contains causal keywords."""
    causal_keywords = ["led to", "caused", "resulted in", "triggered", "sparked",
                       "prompted", "motivated", "precipitated", "provoked",
                       "was followed by", "subsequently"]
    count = 0

    # Group events by year
    by_year: dict[str, list[dict]] = {}
    for ev in events:
        year = ev["date"][:4] if ev["date"] and len(ev["date"]) >= 4 else ""
        if year:
            by_year.setdefault(year, []).append(ev)

    with driver.session() as session:
        for year, year_events in by_year.items():
            for i, ev_a in enumerate(year_events):
                body_a = (ev_a.get("preview") or "").lower()
                for ev_b in year_events[i + 1:]:
                    body_b = (ev_b.get("preview") or "").lower()
                    text = body_a + " " + body_b
                    if any(kw in text for kw in causal_keywords):
                        session.run("""
                            MATCH (a:Event {name: $a_name})
                            MATCH (b:Event {name: $b_name})
                            MERGE (a)-[r:CAUSED]->(b)
                            ON CREATE SET r.confidence = 0.6, r.inferred = true
                        """, a_name=ev_a["name"], b_name=ev_b["name"])
                        count += 1

    return count
