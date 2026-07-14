import os
import re
import logging
import yaml
from typing import Dict, List, Any, Tuple, Optional
from neo4j import Driver
from src.knowledge_graph.connection import neo4j_conn
from src.cache import cache_decorator
from src.config import settings

logger = logging.getLogger("chickensoup.neo4j.ingest")

# Allowlist of valid Neo4j labels — prevents Cypher injection via user-controlled tags
VALID_LABELS = frozenset({"Person", "Place", "Concept", "Object", "Project", "Event", "Entity", "Paper", "QuantumPlatform", "Algorithm"})

# Tag-to-label mapping for entity pages
category_map = {
    "person": "Person", "people": "Person", "whistleblower": "Person",
    "scientist": "Person", "researcher": "Person", "witness": "Person",
    "witnesses": "Person", "military": "Person", "agent": "Person",
    "place": "Place", "location": "Place", "locations": "Place",
    "area": "Place", "country": "Place", "city": "Place",
    "event": "Event", "events": "Event", "crash": "Event",
    "incident": "Event", "encounter": "Event", "sighting": "Event",
    "accident": "Event", "recovery": "Event", "landing": "Event",
    "concept": "Concept", "theory": "Concept", "idea": "Concept",
    "principle": "Concept", "model": "Concept", "framework": "Concept",
    "project": "Project", "program": "Project", "experiment": "Project",
    "mission": "Project", "operation": "Project",
    "object": "Object", "craft": "Object", "artifact": "Object",
    "device": "Object", "technology": "Object", "weapon": "Object",
    "material": "Object", "element": "Object",
}

def _sanitize_label(label: str) -> str:
    """Validate a label against the allowlist. Returns 'Entity' if invalid."""
    return label if label in VALID_LABELS else "Entity"

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
    # Entity pairs (base label, catches everything)
    ("Entity", "Entity"): {"valid": ["RELATED_TO", "REFERENCES", "LINKS_TO"], "default": "RELATED_TO"},
    ("Entity", "Concept"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Concept", "Entity"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Entity", "Person"): {"valid": ["MENTIONS", "DISCUSSES", "REFERENCES"], "default": "REFERENCES"},
    ("Person", "Entity"): {"valid": ["MENTIONS", "DISCUSSES", "REFERENCES"], "default": "REFERENCES"},
    ("Entity", "Project"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Project", "Entity"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Entity", "Object"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Object", "Entity"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Entity", "Event"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Event", "Entity"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    ("Entity", "Place"): {"valid": ["REFERENCES", "LOCATED_IN", "DISCUSSES"], "default": "REFERENCES"},
    ("Place", "Entity"): {"valid": ["REFERENCES", "DISCUSSES", "MENTIONS"], "default": "REFERENCES"},
    # Additional cross-label pairs
    ("Concept", "Project"): {"valid": ["RELATED_TO", "INFORMS", "PRECEDES"], "default": "RELATED_TO"},
    ("Project", "Project"): {"valid": ["RELATED_TO", "DEPENDS_ON", "PRECEDES", "EXTENDS"], "default": "RELATED_TO"},
    ("Concept", "Object"): {"valid": ["RELATED_TO", "DESCRIBES", "REFERENCES"], "default": "RELATED_TO"},
    ("Object", "Concept"): {"valid": ["RELATED_TO", "REFERENCES", "IMPLEMENTS"], "default": "RELATED_TO"},
    ("Person", "Person"): {"valid": ["RELATED_TO", "COLLABORATED_WITH", "MENTORED_BY", "EMPLOYED_BY"], "default": "RELATED_TO"},
    ("Person", "Object"): {"valid": ["RELATED_TO", "CREATED", "RESEARCHED", "USED"], "default": "RELATED_TO"},
    ("Object", "Person"): {"valid": ["RELATED_TO", "CREATED_BY", "USED_BY", "RESEARCHED_BY"], "default": "RELATED_TO"},
    ("Event", "Event"): {"valid": ["RELATED_TO", "PRECEDED_BY", "FOLLOWED_BY", "CAUSED"], "default": "RELATED_TO"},
    ("Event", "Concept"): {"valid": ["RELATED_TO", "DEMONSTRATES", "EXEMPLIFIES"], "default": "RELATED_TO"},
    ("Concept", "Event"): {"valid": ["RELATED_TO", "CONTEXT_FOR", "REFERENCES"], "default": "RELATED_TO"},
    ("Place", "Place"): {"valid": ["RELATED_TO", "LOCATED_IN", "NEAR"], "default": "RELATED_TO"},
    ("Place", "Object"): {"valid": ["RELATED_TO", "LOCATED_IN", "STORED_IN"], "default": "RELATED_TO"},
    ("Object", "Object"): {"valid": ["RELATED_TO", "PART_OF", "USED_WITH"], "default": "RELATED_TO"},
    ("Project", "Person"): {"valid": ["MEMBER_OF", "EMPLOYED_BY", "CONTRIBUTED_TO"], "default": "CONTRIBUTED_TO"},
    ("Project", "Event"): {"valid": ["RELATED_TO", "PRECEDED_BY", "CONTEXT_FOR"], "default": "RELATED_TO"},
    ("Event", "Project"): {"valid": ["RELATED_TO", "CONTEXT_FOR", "PRECEDED"], "default": "RELATED_TO"},
    ("Place", "Person"): {"valid": ["VISITED", "BORN_IN", "LOCATED_AT"], "default": "LOCATED_AT"},
    ("Place", "Event"): {"valid": ["LOCATION_OF", "OCCURRED_AT", "RELATED_TO"], "default": "LOCATION_OF"},
    ("Object", "Event"): {"valid": ["RELATED_TO", "USED_IN", "EVIDENCE_FOR"], "default": "RELATED_TO"},
    ("Event", "Object"): {"valid": ["RELATED_TO", "INVOLVED", "USED"], "default": "RELATED_TO"},
    ("Place", "Project"): {"valid": ["RELATED_TO", "LOCATION_OF", "HOSTS"], "default": "RELATED_TO"},
    ("Object", "Project"): {"valid": ["USES", "MANUFACTURES", "REVERSE_ENGINEERS", "RELATED_TO"], "default": "RELATED_TO"},
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

def _resolve_wiki_root() -> str:
    """Resolve the wiki root directory from settings."""
    wiki_dir = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_dir):
        # Resolve relative to project root (two levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wiki_dir = os.path.join(project_root, wiki_dir)
    return wiki_dir

def _normalize_node_name(name: str) -> str:
    """Normalize a node name for deduplication: lowercase, collapse whitespace, strip."""
    if not name:
        return name
    return " ".join(name.lower().split())


def _resolve_target_wiki_file(name: str) -> Optional[str]:
    """Check if a target name corresponds to a wiki page file."""
    wiki_root = _resolve_wiki_root()
    slug = name.lower().replace(" ", "-")
    for subdir in ["entities", "concepts", "projects"]:
        file_path = os.path.join(wiki_root, subdir, f"{slug}.md")
        if os.path.exists(file_path):
            return file_path
    return None


def infer_node_label(name: str) -> str:
    """
    Inspects the local wiki folder structure to pre-infer the primary label of a target node.
    Uses the shared category_map for tag-to-label resolution.
    """
    wiki_root = _resolve_wiki_root()
    clean_name = name.lower().replace(" ", "-")
    for subdir, label in [("entities", "Entity"), ("concepts", "Concept"), ("projects", "Project")]:
        file_path = os.path.join(wiki_root, subdir, f"{clean_name}.md")
        if os.path.exists(file_path):
            if subdir == "entities":
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        meta, _ = parse_markdown_frontmatter(f.read())
                        tags = meta.get("tags", [])
                        tag_strings = set(str(t).lower() for t in tags)
                        for tag in sorted(tag_strings, key=len, reverse=True):
                            if tag in category_map:
                                return category_map[tag]
                except Exception:
                    pass
                return "Entity"
            return label
    return "Entity"

@cache_decorator(prefix="llm", ttl=3600)
def _query_llm_for_edge_type(source: str, source_label: str, target: str, target_label: str, body: str) -> Tuple[str, bool]:
    """
    Classify relationship type using pure heuristics (no LLM).
    Returns (relationship_type, should_reverse_direction).

    The LLM path was removed because:
      - It made N sequential calls per page (up to 35 min per page)
      - 5+ out-of-schema types were returned, defaulted to REFERENCES anyway
      - Heuristics already cover 17+ keyword patterns with equivalent accuracy
    """
    reverse = False
    s_label = source_label
    t_label = target_label

    if (t_label, s_label) in SCHEMA_RELATIONSHIPS and (s_label, t_label) not in SCHEMA_RELATIONSHIPS:
        s_label, t_label = t_label, s_label
        source, target = target, source
        reverse = True

    pair = (s_label, t_label)
    options = SCHEMA_RELATIONSHIPS.get(pair, {"valid": ["RELATED_TO"], "default": "RELATED_TO"})
    valid_options = options["valid"]
    default_option = options["default"]

    return _fallback_heuristic_edge_type(source, source_label, target, target_label, body, valid_options, default_option)


def _fallback_heuristic_edge_type(
    source: str, source_label: str,
    target: str, target_label: str,
    body: str,
    valid_options: List[str],
    default_option: str
) -> Tuple[str, bool]:
    """Heuristic fallback when LLM is unavailable or all retries are exhausted."""
    body_lower = body.lower()
    for keyword, rel, options_field in [
        ("worked", "EMPLOYED_BY", ["EMPLOYED_BY", "WORKED_AT"]),
        ("employ", "EMPLOYED_BY", ["EMPLOYED_BY", "WORKED_AT"]),
        ("testified", "TESTIFIED_AT", ["TESTIFIED_AT"]),
        ("proposed", "PROPOSED", ["PROPOSED"]),
        ("developed", "PROPOSED", ["PROPOSED"]),
        ("formulated", "PROPOSED", ["PROPOSED"]),
        ("implements", "IMPLEMENTS", ["IMPLEMENTS"]),
        ("uses", "USES", ["USES"]),
        ("utilizes", "USES", ["USES"]),
        ("occurred", "OCCURRED_AT", ["OCCURRED_AT"]),
        ("crashed", "OCCURRED_AT", ["OCCURRED_AT"]),
        ("landed", "OCCURRED_AT", ["OCCURRED_AT"]),
        ("extend", "EXTENDS", ["EXTENDS"]),
        ("extends", "EXTENDS", ["EXTENDS"]),
        ("extension", "EXTENDS", ["EXTENDS"]),
        ("build on", "BASED_ON", ["BASED_ON", "INFLUENCED"]),
        ("built on", "BASED_ON", ["BASED_ON", "INFLUENCED"]),
        ("based on", "BASED_ON", ["BASED_ON", "INFLUENCED"]),
        ("contrast", "CONTRADICTS", ["CONTRADICTS"]),
        ("contradict", "CONTRADICTS", ["CONTRADICTS"]),
        ("equivalent", "EQUIVALENT_TO", ["EQUIVALENT_TO"]),
        ("influence", "INFLUENCED", ["INFLUENCED"]),
        ("influenced", "INFLUENCED", ["INFLUENCED"]),
        ("reference", "REFERENCES", ["REFERENCES"]),
        ("refer to", "REFERENCES", ["REFERENCES"]),
        ("mention", "REFERENCES", ["REFERENCES"]),
        ("discuss", "REFERENCES", ["REFERENCES"]),
        ("discussed", "REFERENCES", ["REFERENCES"]),
        ("cite", "REFERENCES", ["REFERENCES"]),
        ("citation", "REFERENCES", ["REFERENCES"]),
    ]:
        if keyword in body_lower and rel in valid_options:
            return rel, False
    return default_option, False

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
    
    # Normalize title for deduplication
    title = _normalize_node_name(title)

    # Determine primary label (uses module-level category_map)
    primary_label = "Entity"
    tag_strings = set(str(t).lower() for t in tags)
    for tag in sorted(tag_strings, key=len, reverse=True):
        if tag in category_map:
            primary_label = _sanitize_label(category_map[tag])
            break

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
        RETURN elementId(n)
        """
        preview = body[:300] + "..." if len(body) > 300 else body
        session.run(primary_query, name=title, tags=tags, sources=sources, preview=preview)
        nodes_count += 1

        primary_label = _sanitize_label(primary_label)
        if primary_label != "Entity":
            session.run(f"MATCH (n:Entity {{name: $name}}) SET n:{primary_label}", name=title)

        # Ingest target links
        for target in all_targets:
            target = _normalize_node_name(target)
            if not target or target == title:
                continue

            # Only create target node if it corresponds to a wiki page
            if not _resolve_target_wiki_file(target):
                logger.debug(
                    "Skipping placeholder node for unresolvable target '%s' (source: %s)",
                    target, title
                )
                continue

            target_label = _sanitize_label(infer_node_label(target))

            # Create referenced node
            target_query = """
            MERGE (t:Entity {name: $target_name})
            ON CREATE SET t.confidence = 0.5
            RETURN elementId(t)
            """
            session.run(target_query, target_name=target)
            nodes_count += 1

            if target_label != "Entity":
                session.run(f"MATCH (t:Entity {{name: $target_name}}) SET t:{target_label}", target_name=target)

            # Classify edge type
            rel_type, reverse = _query_llm_for_edge_type(title, primary_label, target, target_label, body)

            # Draw relationship in the correct semantic direction using :Entity matching
            if reverse:
                rel_query = f"""
                MATCH (n:Entity {{name: $name}})
                MATCH (t:Entity {{name: $target_name}})
                MERGE (t)-[r:{rel_type}]->(n)
                ON CREATE SET r.confidence = 0.8
                RETURN elementId(r)
                """
            else:
                rel_query = f"""
                MATCH (n:Entity {{name: $name}})
                MATCH (t:Entity {{name: $target_name}})
                MERGE (n)-[r:{rel_type}]->(t)
                ON CREATE SET r.confidence = 0.8
                RETURN elementId(r)
                """
            session.run(rel_query, name=title, target_name=target)
            rels_count += 1

    return nodes_count, rels_count
