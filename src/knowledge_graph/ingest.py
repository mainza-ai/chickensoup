import os
import re
import logging
import yaml
from typing import Dict, List, Any, Tuple, Optional
from neo4j import Driver
from src.knowledge_graph.connection import neo4j_conn
from src.cache import cache_store, cache_decorator
from src.config import settings
from src.wiki.cleanup import ENGINEERING_TAGS, CONTENT_TAGS

logger = logging.getLogger("chickensoup.neo4j.ingest")

VALID_LABELS = frozenset({"Person", "Place", "Concept", "Object", "Project", "Event", "Entity", "Paper", "QuantumPlatform", "Algorithm"})

_INFERENCE_WEIGHTS = {
    "Person": {"strong": ["person", "people", "whistleblower", "witness", "witnesses", "scientist", "researcher", "physicist"], "weak": ["agent", "military"], "name_patterns": [r"\b(?:dr|prof|senator|ambassador|gen|adm)\b"]},
    "Place": {"strong": ["place", "location", "locations", "country", "city", "area", "base", "facility"], "weak": []},
    "Event": {"strong": ["event", "events", "incident", "crash", "sighting", "hearing", "encounter", "accident", "landing", "disclosure"], "weak": []},
    "Project": {"strong": ["project", "program", "experiment", "mission", "operation"], "weak": []},
    "Object": {"strong": ["object", "craft", "artifact", "device", "material", "element", "weapon", "technology"], "weak": []},
}

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
    link_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    return [link.strip() for link in link_pattern.findall(content)]

def _resolve_wiki_root() -> str:
    wiki_dir = settings.WIKI_DATA_DIR
    if not os.path.isabs(wiki_dir):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wiki_dir = os.path.join(project_root, wiki_dir)
    return wiki_dir

def _resolve_target_wiki_file(name: str) -> Optional[str]:
    wiki_root = _resolve_wiki_root()
    candidates = set()
    base = name.lower().strip()
    candidates.add(base)
    candidates.add(base.replace(" ", "-"))
    candidates.add(base.replace("-", " "))
    candidates.add(base.replace("-", "").replace(" ", ""))
    for subdir in ("entities", "concepts", "projects", "raw", "raw/drafts"):
        dirpath = os.path.join(wiki_root, subdir)
        if not os.path.isdir(dirpath):
            continue
        for fname in os.listdir(dirpath):
            if not fname.endswith(".md"):
                continue
            fstem = fname[:-3].lower()
            if fstem in candidates or fstem.replace("-", "") == base.replace("-", "").replace(" ", ""):
                return os.path.join(dirpath, fname)
    return None

def _read_target_display_name(name: str) -> str:
    filepath = _resolve_target_wiki_file(name)
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                meta, _ = parse_markdown_frontmatter(f.read())
            if meta.get("title"):
                return meta["title"]
        except Exception:
            pass
    return name

def _sanitize_label(label: str) -> str:
    return label if label in VALID_LABELS else "Entity"

def _infer_primary_label(name: str, tags: List[str], body: str = "") -> str:
    scores = {label: 0.0 for label in ["Concept", "Person", "Place", "Event", "Project", "Object"]}
    tag_set = set(str(t).lower() for t in tags)
    name_lower = name.lower()
    body_lower = (body or "").lower()

    for pat in [r"\b(?:dr|prof|senator|ambassador|gen|adm)\b"]:
        if re.search(pat, name_lower):
            scores["Person"] += 3.0
    # Name looks like a person: 2+ words where first is title or name-like
    name_words = name.split()
    person_name_patterns = [
        r"^[A-Z][a-z]+ [A-Z][a-z]+$",     # "Bob Lazar", "David Grusch"
        r"^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$",  # "John A. Smith"
        r"^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$",  # "Thomas Townsend Brown"
    ]
    display_name = " ".join(name_words)
    if any(re.match(p, display_name) for p in person_name_patterns):
        scores["Person"] += 2.0

    for label, signals in _INFERENCE_WEIGHTS.items():
        for tag in signals["strong"]:
            if tag in tag_set:
                scores[label] += 2.0
        for tag in signals["weak"]:
            if tag in tag_set:
                scores[label] += 0.3

    if body_lower.count("lived in") + body_lower.count("was born") > 2:
        scores["Person"] += 1.0
    if body_lower.count("project") + body_lower.count("program") > 3:
        scores["Project"] += 1.0
    if body_lower.count("area 51") > 0 or body_lower.count("located at") > 2:
        scores["Place"] += 0.5

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Entity"

def _normalize_node_name(name: str) -> str:
    if not name:
        return name
    return " ".join(name.lower().split())

def _is_engineering_only(tags: List[str]) -> bool:
    tag_set = set(str(t).lower() for t in tags)
    is_eng = bool(tag_set & ENGINEERING_TAGS)
    has_content = bool(tag_set & CONTENT_TAGS)
    return is_eng and not has_content


def _seed_fallback_retry(slug: str):
    try:
        if cache_store.redis_client:
            cache_store.redis_client.sadd("retry:fallback", slug)
            cache_store.redis_client.expire("retry:fallback", 2592000)
    except Exception:
        pass


@cache_decorator(prefix="llm", ttl=3600)
def _query_llm_for_edge_type(source: str, source_label: str, target: str, target_label: str, body: str) -> Tuple[str, bool]:
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
    metadata, body = parse_markdown_frontmatter(content)

    tags = [str(t) for t in metadata.get("tags", default_tags or [])]
    sources = [str(s) for s in metadata.get("sources", default_sources or [])]
    related = metadata.get("related", [])

    # P3: Engineering-only gate — skip Neo4j ingest
    if _is_engineering_only(tags):
        logger.debug(f"Skipping Neo4j ingest for engineering-only page '{title}'")
        return 0, 0

    # P1: Use frontmatter title as canonical display name
    display_name = metadata.get("title") or title
    display_name = display_name.strip()
    node_name = _normalize_node_name(display_name)

    # P2: Infer label using multi-heuristic scorer
    primary_label = _infer_primary_label(display_name, tags, body)
    primary_label = _sanitize_label(primary_label)

    # P7: Detect fallback (pages from _fallback_analysis carry "fallback" tag)
    is_fallback = "fallback" in [str(t).lower() for t in tags]

    # P4: Read protected flag
    protected = bool(metadata.get("protected", False))

    wiki_links = extract_wiki_links(body)
    all_targets = list(set(related + wiki_links))
    all_targets = [str(t) for t in all_targets]

    nodes_count = 0
    rels_count = 0

    with driver.session() as session:
        primary_query = """
        MERGE (n:Entity {name: $name})
        ON CREATE SET
          n.display_name = $display,
          n.tags = $tags,
          n.sources = $sources,
          n.content_preview = $preview,
          n.confidence = 1.0,
          n.fallback = $fallback,
          n.protected = $protected
        ON MATCH SET
          n.display_name = $display,
          n.tags = $tags,
          n.sources = $sources,
          n.content_preview = $preview,
          n.fallback = $fallback,
          n.protected = $protected
        RETURN elementId(n)
        """
        preview = body[:300] + "..." if len(body) > 300 else body
        session.run(primary_query, name=node_name, display=display_name, tags=tags, sources=sources, preview=preview, fallback=is_fallback, protected=protected)
        nodes_count += 1

        if primary_label != "Entity":
            session.run(f"MATCH (n:Entity {{name: $name}}) SET n:{primary_label}", name=node_name)

        if is_fallback:
            slug = display_name.lower().replace(" ", "-")
            _seed_fallback_retry(slug)

        for target in all_targets:
            target_display = _read_target_display_name(target)
            target_name = _normalize_node_name(target_display)
            if not target_name or target_name == node_name:
                continue

            if not _resolve_target_wiki_file(target):
                logger.debug("Skipping placeholder node for unresolvable target '%s' (source: %s)", target, display_name)
                continue

            target_label = _sanitize_label(_infer_primary_label(target_display, []))

            target_query = """
            MERGE (t:Entity {name: $target_name})
            ON CREATE SET t.display_name = $target_display, t.confidence = 0.5
            RETURN elementId(t)
            """
            session.run(target_query, target_name=target_name, target_display=target_display)
            nodes_count += 1

            if target_label != "Entity":
                session.run(f"MATCH (t:Entity {{name: $target_name}}) SET t:{target_label}", target_name=target_name)

            rel_type, reverse = _query_llm_for_edge_type(display_name, primary_label, target_display, target_label, body)

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
            session.run(rel_query, name=node_name, target_name=target_name)
            rels_count += 1

    return nodes_count, rels_count
