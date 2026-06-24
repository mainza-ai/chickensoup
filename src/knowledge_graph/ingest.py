import re
import logging
import yaml
import json
import urllib.request
from typing import Dict, List, Any, Tuple
from neo4j import Driver
from src.knowledge_graph.connection import neo4j_conn
from src.discovery import discover_active_provider

logger = logging.getLogger("chickensoup.neo4j.ingest")

def parse_markdown_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parses YAML frontmatter from a markdown string.
    Returns a tuple of (metadata_dict, remaining_content_str).
    """
    yaml_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = yaml_pattern.match(content)
    if match:
        frontmatter_text = match.group(1)
        try:
            metadata = yaml.safe_load(frontmatter_text)
            if isinstance(metadata, dict):
                remaining_content = content[match.end():]
                return metadata, remaining_content
        except Exception as e:
            logger.warning(f"Error parsing frontmatter YAML: {e}")
    
    return {}, content

def extract_wiki_links(content: str) -> List[str]:
    """
    Extracts Obsidian-style links: [[WikiLink]] or [[WikiLink|Custom Text]].
    """
    link_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    return [link.strip() for link in link_pattern.findall(content)]

def _query_llm_for_edge_type(source: str, source_label: str, target: str, body: str) -> str:
    """Probes the active local LLM to promote generic RELATED_TO edges to a specific typed edge."""
    provider, base_url, models = discover_active_provider()
    if provider == "simulated" or not models:
        # Classical heuristic mapping based on content keywords
        body_lower = body.lower()
        if source_label == "Person":
            if "worked at" in body_lower or "employed by" in body_lower or "researcher at" in body_lower or "scientist at" in body_lower:
                return "WORKED_AT"
            if "testified" in body_lower or "congressional testimony" in body_lower or "hearing" in body_lower:
                return "TESTIFIED_AT"
        if "claimed by" in body_lower or "according to" in body_lower:
            return "CLAIMED_BY"
        if "part of" in body_lower or "division of" in body_lower:
            return "PART_OF"
        if source_label in ["Project", "Object"]:
            if "uses" in body_lower or "utilizes" in body_lower or "based on" in body_lower:
                return "USES"
        if "implements" in body_lower or "realizes" in body_lower:
            return "IMPLEMENTS"
        return "RELATED_TO"

    url = f"{base_url}/chat/completions"
    prompt = f"""
    You are an expert knowledge graph schema engineer. Given the source node, its label, the target node, and the text context, determine the single most appropriate relationship type between the source and target.

    Options:
    - WORKED_AT (e.g. Person worked at Organization/Company/Base)
    - TESTIFIED_AT (e.g. Person testified at Hearing/Congress/Event)
    - CLAIMED_BY (e.g. Concept or Event claimed by Person)
    - PART_OF (e.g. Project part of Program, or Place part of Region)
    - USES (e.g. Project uses Algorithm/Platform)
    - IMPLEMENTS (e.g. Algorithm implements Concept)
    - RELATED_TO (generic fallback)

    Source Name: "{source}" (Label: {source_label})
    Target Name: "{target}"
    Context:
    {body[:500]}

    Return ONLY a JSON object:
    {{
        "relationship": "WORKED_AT" | "TESTIFIED_AT" | "CLAIMED_BY" | "PART_OF" | "USES" | "IMPLEMENTS" | "RELATED_TO"
    }}
    """
    payload = {
        "model": models[0],
        "messages": [
            {"role": "system", "content": "You are a precise JSON classifier."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30.0) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                result = json.loads(content)
                return result.get("relationship", "RELATED_TO")
    except Exception as e:
        logger.debug(f"LLM edge promotion failed: {e}. Using heuristic fallback.")

    # Heuristic fallback if request fails
    body_lower = body.lower()
    if source_label == "Person":
        if "worked at" in body_lower or "employed by" in body_lower or "researcher at" in body_lower or "scientist at" in body_lower:
            return "WORKED_AT"
        if "testified" in body_lower or "congressional testimony" in body_lower or "hearing" in body_lower:
            return "TESTIFIED_AT"
    if "claimed by" in body_lower or "according to" in body_lower:
        return "CLAIMED_BY"
    if "part of" in body_lower or "division of" in body_lower:
        return "PART_OF"
    if source_label in ["Project", "Object"]:
        if "uses" in body_lower or "utilizes" in body_lower or "based on" in body_lower:
            return "USES"
    if "implements" in body_lower or "realizes" in body_lower:
        return "IMPLEMENTS"
    return "RELATED_TO"

def ingest_wiki_page(
    driver: Driver,
    title: str,
    content: str,
    default_tags: List[str] = None,
    default_sources: List[str] = None
) -> Tuple[int, int]:
    """
    Parses a wiki page (markdown) and ingests it into Neo4j.
    Creates a main node for the page and creates relationships to any linked concepts/entities.
    Promotes generic RELATED_TO links into typed relationships using an LLM classifier or heuristics.
    Returns:
        Tuple of (nodes_created_or_updated, relationships_created)
    """
    metadata, body = parse_markdown_frontmatter(content)
    
    # Determine tags, sources, and labels from metadata or defaults
    # Convert tags and sources to clean lists of strings to prevent Neo4j mixed type array errors
    tags = [str(t) for t in metadata.get("tags", default_tags or [])]
    sources = [str(s) for s in metadata.get("sources", default_sources or [])]
    related = metadata.get("related", [])
    
    # Determine the primary node label (default to Concept or Entity)
    primary_label = "Entity"
    if "concept" in tags:
        primary_label = "Concept"
    elif "project" in tags:
        primary_label = "Project"
    elif "person" in tags:
        primary_label = "Person"
    elif "place" in tags:
        primary_label = "Place"
    elif "event" in tags:
        primary_label = "Event"

    wiki_links = extract_wiki_links(body)
    all_targets = list(set(related + wiki_links))

    # Convert all targets to strings as well
    all_targets = [str(t) for t in all_targets]

    nodes_count = 0
    rels_count = 0

    with driver.session() as session:
        # Create or update the primary node by merging on Entity label first to avoid constraint validation errors
        primary_query = """
        MERGE (n:Entity {name: $name})
        ON CREATE SET n.tags = $tags, n.sources = $sources, n.content_preview = $preview, n.confidence = 1.0
        ON MATCH SET n.tags = $tags, n.sources = $sources, n.content_preview = $preview
        RETURN id(n)
        """
        preview = body[:300] + "..." if len(body) > 300 else body
        session.run(primary_query, name=title, tags=tags, sources=sources, preview=preview)
        nodes_count += 1

        # Add the specific label if it's different from Entity
        if primary_label != "Entity":
            session.run(f"MATCH (n:Entity {{name: $name}}) SET n:{primary_label}", name=title)

        # For every referenced link, create the linked node (default: Entity) and relate it
        for target in all_targets:
            if not target or target == title:
                continue
            
            # Create referenced entity if not exists
            target_query = """
            MERGE (t:Entity {name: $target_name})
            ON CREATE SET t.confidence = 0.5
            RETURN id(t)
            """
            session.run(target_query, target_name=target)
            nodes_count += 1
            
            # Determine promoted edge type
            rel_type = _query_llm_for_edge_type(title, primary_label, target, body)
            
            # Create bi-directional or directed relationship
            rel_query = f"""
            MATCH (n:{primary_label} {{name: $name}})
            MATCH (t:Entity {{name: $target_name}})
            MERGE (n)-[r:{rel_type}]->(t)
            ON CREATE SET r.confidence = 0.8
            RETURN id(r)
            """
            session.run(rel_query, name=title, target_name=target)
            rels_count += 1

    return nodes_count, rels_count
