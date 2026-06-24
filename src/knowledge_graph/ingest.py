import os
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

# Enforce a strict type-matching schema layout
SCHEMA_RELATIONSHIPS = {
    ("Person", "Place"): {"valid": ["VISITED", "BORN_IN", "LOCATED_AT", "TESTIFIED_AT"], "default": "LOCATED_AT"},
    ("Person", "Project"): {"valid": ["MEMBER_OF", "LEAD_ON", "CONTRIBUTED_TO", "FOUNDED"], "default": "CONTRIBUTED_TO"},
    ("Person", "Concept"): {"valid": ["PROPOSED", "RESEARCHED", "CRITICIZED", "SUPPORTED"], "default": "RESEARCHED"},
    ("Person", "Organization"): {"valid": ["EMPLOYED_BY", "FOUNDED", "CONSULTED_FOR", "MEMBER_OF"], "default": "EMPLOYED_BY"},
    ("Person", "Event"): {"valid": ["WITNESSED", "PARTICIPATED_IN", "DISCLOSED"], "default": "PARTICIPATED_IN"},
    ("Project", "Concept"): {"valid": ["IMPLEMENTS", "BASED_ON", "TESTS"], "default": "BASED_ON"},
    ("Project", "Object"): {"valid": ["USES", "MANUFACTURES", "REVERSE_ENGINEERS"], "default": "USES"},
    ("Concept", "Concept"): {"valid": ["EXTENDS", "CONTRADICTS", "EQUIVALENT_TO", "INFLUENCED"], "default": "INFLUENCED"},
    ("Event", "Place"): {"valid": ["OCCURRED_AT", "INVESTIGATED_IN"], "default": "OCCURRED_AT"},
    ("Event", "Person"): {"valid": ["INVOLVED", "WITNESSED_BY", "CLAIMED_BY"], "default": "INVOLVED"},
}

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

def infer_node_label(name: str) -> str:
    """
    Inspects the local wiki folder structure to pre-infer the primary label of a target node.
    """
    wiki_root = "/Users/mck/Desktop/chickensoup/wiki"
    clean_name = name.lower().replace(" ", "-")
    for subdir, label in [("entities", "Entity"), ("concepts", "Concept"), ("projects", "Project")]:
        file_path = os.path.join(wiki_root, subdir, f"{clean_name}.md")
        if os.path.exists(file_path):
            if subdir == "entities":
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        meta, _ = parse_markdown_frontmatter(f.read())
                        tags = meta.get("tags", [])
                        if "person" in tags:
                            return "Person"
                        if "place" in tags:
                            return "Place"
                        if "event" in tags:
                            return "Event"
                        if "object" in tags:
                            return "Object"
                except Exception:
                    pass
                return "Entity"
            return label
    return "Entity"

def _query_llm_for_edge_type(source: str, source_label: str, target: str, target_label: str, body: str) -> Tuple[str, bool]:
    """
    Probes the active LLM (or heuristics) to determine the best relationship type.
    Returns (relationship_type, should_reverse_direction).
    """
    reverse = False
    s_label = source_label
    t_label = target_label
    
    # If the target-to-source fits a schema matrix entry, swap for semantic analysis and reverse later
    if (t_label, s_label) in SCHEMA_RELATIONSHIPS and (s_label, t_label) not in SCHEMA_RELATIONSHIPS:
        s_label, t_label = t_label, s_label
        source, target = target, source
        reverse = True
        
    pair = (s_label, t_label)
    options = SCHEMA_RELATIONSHIPS.get(pair, {"valid": ["RELATED_TO"], "default": "RELATED_TO"})
    valid_options = options["valid"]
    default_option = options["default"]
    
    provider, base_url, models = discover_active_provider()
    if provider == "simulated" or not models:
        # Refined keyword heuristical fallbacks constrained by schema options
        body_lower = body.lower()
        if "WORKED_AT" in valid_options or "EMPLOYED_BY" in valid_options:
            if "worked" in body_lower or "employed" in body_lower or "researcher" in body_lower:
                return "EMPLOYED_BY" if "EMPLOYED_BY" in valid_options else "WORKED_AT", reverse
        if "TESTIFIED_AT" in valid_options:
            if "testified" in body_lower or "testimony" in body_lower:
                return "TESTIFIED_AT", reverse
        if "PROPOSED" in valid_options:
            if "proposed" in body_lower or "developed" in body_lower or "formulated" in body_lower:
                return "PROPOSED", reverse
        if "IMPLEMENTS" in valid_options:
            if "implements" in body_lower or "realizes" in body_lower:
                return "IMPLEMENTS", reverse
        if "USES" in valid_options:
            if "uses" in body_lower or "utilizes" in body_lower:
                return "USES", reverse
        if "OCCURRED_AT" in valid_options:
            if "occurred" in body_lower or "crashed" in body_lower or "landed" in body_lower:
                return "OCCURRED_AT", reverse
                
        return default_option, reverse

    url = f"{base_url}/chat/completions"
    options_str = "\n".join([f"- {opt}" for opt in valid_options])
    prompt = f"""
    You are an expert knowledge graph schema engineer. Given the source node, its label, the target node, its label, and the context, determine the single most appropriate relationship type between them.
    
    Permitted Options for a connection from {s_label} to {t_label}:
    {options_str}
    
    Source Name: "{source}" (Label: {s_label})
    Target Name: "{target}" (Label: {t_label})
    Context:
    {body[:500]}
    
    Return ONLY a JSON object:
    {{
        "relationship": "<One of the permitted options listed above>"
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
                rel = result.get("relationship", default_option)
                if rel in valid_options:
                    return rel, reverse
    except Exception as e:
        logger.debug(f"LLM edge promotion failed: {e}. Using heuristic fallback.")
        
    return default_option, reverse

def ingest_wiki_page(
    driver: Driver,
    title: str,
    content: str,
    default_tags: List[str] = None,
    default_sources: List[str] = None
) -> Tuple[int, int]:
    """
    Parses a wiki page (markdown) and ingests it into Neo4j using validation matrices.
    """
    metadata, body = parse_markdown_frontmatter(content)
    
    tags = [str(t) for t in metadata.get("tags", default_tags or [])]
    sources = [str(s) for s in metadata.get("sources", default_sources or [])]
    related = metadata.get("related", [])
    
    # Determine primary label
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
    all_targets = [str(t) for t in all_targets]

    nodes_count = 0
    rels_count = 0

    with driver.session() as session:
        # Create or update primary node
        primary_query = """
        MERGE (n:Entity {name: $name})
        ON CREATE SET n.tags = $tags, n.sources = $sources, n.content_preview = $preview, n.confidence = 1.0
        ON MATCH SET n.tags = $tags, n.sources = $sources, n.content_preview = $preview
        RETURN id(n)
        """
        preview = body[:300] + "..." if len(body) > 300 else body
        session.run(primary_query, name=title, tags=tags, sources=sources, preview=preview)
        nodes_count += 1

        if primary_label != "Entity":
            session.run(f"MATCH (n:Entity {{name: $name}}) SET n:{primary_label}", name=title)

        # Ingest target links
        for target in all_targets:
            if not target or target == title:
                continue
            
            target_label = infer_node_label(target)
            
            # Create referenced node
            target_query = """
            MERGE (t:Entity {name: $target_name})
            ON CREATE SET t.confidence = 0.5
            RETURN id(t)
            """
            session.run(target_query, target_name=target)
            nodes_count += 1
            
            if target_label != "Entity":
                session.run(f"MATCH (t:Entity {{name: $target_name}}) SET t:{target_label}", target_name=target)

            # Classify edge type
            rel_type, reverse = _query_llm_for_edge_type(title, primary_label, target, target_label, body)
            
            # Draw relationship in the correct semantic direction
            if reverse:
                rel_query = f"""
                MATCH (n:{primary_label} {{name: $name}})
                MATCH (t:{target_label} {{name: $target_name}})
                MERGE (t)-[r:{rel_type}]->(n)
                ON CREATE SET r.confidence = 0.8
                RETURN id(r)
                """
            else:
                rel_query = f"""
                MATCH (n:{primary_label} {{name: $name}})
                MATCH (t:{target_label} {{name: $target_name}})
                MERGE (n)-[r:{rel_type}]->(t)
                ON CREATE SET r.confidence = 0.8
                RETURN id(r)
                """
            session.run(rel_query, name=title, target_name=target)
            rels_count += 1

    return nodes_count, rels_count
