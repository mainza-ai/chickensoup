---
title: "Neo4j Data Quality Remediation"
tags: [plan, neo4j, data-quality, remediation]
created: 2026-07-14
updated: 2026-07-14
related: [knowledge-graph-schema, integration-architecture]
---

# Neo4j Data Quality Remediation Plan

## Current State (Pre-Fix)

| Metric | Value | Target |
|---|---|---|
| Total nodes | 734 | ~250 (after dedup) |
| Placeholder nodes (confidence=0.5, null data) | 518 (71%) | 0 |
| Duplicate name groups | 197 | 0 |
| Real nodes (confidence=1.0) | 216 | ~250 |
| Total relationships | 3,422 | — |
| `RELATED_TO` (generic fallback) | 3,184 (93%) | <50% |
| Typed relationships | 238 (7%) | >50% |

## Issues Found

### Issue 1: 518 Placeholder Nodes Bloat the Graph

Every unresolvable `[[wikilink]]` creates a dead node via `src/knowledge_graph/ingest.py:308`:

```cypher
MERGE (t:Entity {name: $target_name})
ON CREATE SET t.confidence = 0.5
```

The LLM generates references like `[[Exotic Matter]]`, `[[Metatron]]`, `[[S-4]]` that don't match any wiki page filename. These 518 nodes have null tags, null sources, null content_preview — zero utility.

**Root cause**: Target MERGE creates nodes unconditionally before checking whether the name corresponds to an actual wiki page.

### Issue 2: 197 Duplicate Name Groups

No name normalization before `MERGE`. A single wiki page gets 2-3 Neo4j nodes:
- "AI Navigator" (from title) → `[Concept, Entity]`
- "ai navigator" (from LLM extraction) → `[Concept, Entity]`
- "ai-navigator" (from wikilink) → `[Entity]` (null data)

**Root cause**: `MERGE (t:Entity {name: $target_name})` at `ingest.py:307` stores names as-is from wikilinks. No slugification or case normalization before comparison.

### Issue 3: `infer_node_label` Returns "Entity" for 80%+ of Pages

The function at `ingest.py:73-99` checks only `["person", "place", "event", "object"]` as special tags. Zero wiki pages use any of these exact tags. The actual tags are `["whistleblower"]`, `["area-51"]`, `["ufo", "crash"]` — which should map to Person, Place, Event via `ingest_wiki_page`'s `category_map` (40+ entries).

**Effect**: Bob Lazar (a person with tag "whistleblower") gets label `Entity` instead of `Person`. The label pair becomes `(Concept, Entity)` instead of `(Concept, Person)`.

### Issue 4: Schema Coverage Missing 39 of 49 Label Pairs

`SCHEMA_RELATIONSHIPS` at `ingest.py:25-36` covers only 10 of 49 label pairs that actually appear in Neo4j relationships. The missing 39 pairs — representing 1,852 of 3,422 relationships (54%) — silently fall back to `RELATED_TO`.

**Effect**: `Entity→Entity`, `Entity→Concept`, `Concept→Entity`, `Entity→Person`, and 35 other pairs never get typed relationships.

### Issue 5: LLM Edge Classification Fails Within Covered Pairs

Even for pairs in the schema, typed relationships are rare:
- Concept→Concept: only 5% typed (63 of 1,256)
- Person→Concept: 50% typed (71 of 141)
- Project→Concept: 42% typed (58 of 138)

The 3-retry × 30s LLM timeout (90s total) exhausts retries, falling back to heuristics that only check a handful of verbs.

### Issue 6: Wrong Secondary Labels

12 Person-labeled nodes exist, many incorrect:
- "Area 51" → Person (it's a place)
- "UAP" → Person (it's a phenomenon)
- "UAP Hearings" → Person (it's an event)
- "Ariel School UFO Incident" → Person (it's an event)

**Root cause**: `classify_page_type` at `ingest_agent.py:162` does substring matching (`"person" in text`) — the LLM summary mentioning "a person" triggers false positives.

### Issue 7: Test Pages

`wiki/entities/test-a.md` and `wiki/concepts/test-b.md` on disk, plus their Neo4j counterparts.

## Remediation Phases

### Phase 1a — Fix Label Detection for Targets (`infer_node_label`)

**File**: `src/knowledge_graph/ingest.py`, function `infer_node_label` (line 73)

Reuse `ingest_wiki_page`'s `category_map` (40+ tag→label mappings) instead of the current 4-tag check. After reading the frontmatter tags from the wiki file, iterate through `category_map` sorted by tag length descending (same pattern as `ingest_wiki_page` line 270).

```python
def infer_node_label(name: str) -> str:
    wiki_root = _resolve_wiki_root()
    clean_name = name.lower().replace(" ", "-")
    for subdir, label in [("entities", "Entity"), ("concepts", "Concept"), ("projects", "Project")]:
        file_path = os.path.join(wiki_root, subdir, f"{clean_name}.md")
        if os.path.exists(file_path):
            if subdir == "entities":
                try:
                    with open(file_path) as f:
                        meta, _ = parse_markdown_frontmatter(f.read())
                        tags = meta.get("tags", [])
                        # Use the same category_map as ingest_wiki_page
                        for tag in sorted(set(str(t).lower() for t in tags), key=len, reverse=True):
                            if tag in category_map:
                                return category_map[tag]
                except Exception:
                    pass
            return label
    return "Entity"
```

### Phase 1b — Fix Schema Coverage

**File**: `src/knowledge_graph/ingest.py`, constant `SCHEMA_RELATIONSHIPS` (line 25)

Add every missing label pair. For Entity-involving pairs, inherit valid options from the non-Entity side:

```python
SCHEMA_RELATIONSHIPS = {
    # Existing pairs kept
    ("Person", "Place"): {"valid": ["VISITED", "BORN_IN", "LOCATED_AT", "TESTIFIED_AT"], "default": "LOCATED_AT"},
    ("Person", "Project"): {"valid": ["MEMBER_OF", "LEAD_ON", "CONTRIBUTED_TO", "FOUNDED"], "default": "CONTRIBUTED_TO"},
    ("Person", "Concept"): {"valid": ["PROPOSED", "RESEARCHED", "CRITICIZED", "SUPPORTED"], "default": "RESEARCHED"},
    ("Person", "Event"): {"valid": ["WITNESSED", "PARTICIPATED_IN", "DISCLOSED"], "default": "PARTICIPATED_IN"},
    ("Project", "Concept"): {"valid": ["IMPLEMENTS", "BASED_ON", "TESTS", "USES"], "default": "BASED_ON"},
    ("Project", "Object"): {"valid": ["USES", "MANUFACTURES", "REVERSE_ENGINEERS"], "default": "USES"},
    ("Concept", "Concept"): {"valid": ["EXTENDS", "CONTRADICTS", "EQUIVALENT_TO", "INFLUENCED", "BASED_ON"], "default": "INFLUENCED"},
    ("Event", "Place"): {"valid": ["OCCURRED_AT", "INVESTIGATED_IN"], "default": "OCCURRED_AT"},
    ("Event", "Person"): {"valid": ["INVOLVED", "WITNESSED_BY", "CLAIMED_BY"], "default": "INVOLVED"},
    # New: Entity pairs (Entity is the base label)
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
    # New: Concept pairs
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
```

Key change: Entity-involving pairs now have at minimum `REFERENCES` as a valid option, so the LLM gets called instead of silently defaulting to `RELATED_TO`.

### Phase 1c — Fix Heuristic Fallback

**File**: `src/knowledge_graph/ingest.py`, function `_fallback_heuristic_edge_type` (line 207)

Add keyword matches for Concept→Concept and Entity→Entity pairs:

```python
# Add to the keyword list:
("extend", "EXTENDS", ["EXTENDS"]),
("build on", "BASED_ON", ["BASED_ON", "INFLUENCED"]),
("contrast", "CONTRADICTS", ["CONTRADICTS"]),
("equivalent", "EQUIVALENT_TO", ["EQUIVALENT_TO"]),
("influence", "INFLUENCED", ["INFLUENCED"]),
("based on", "BASED_ON", ["BASED_ON"]),
("derived from", "BASED_ON", ["BASED_ON"]),
("referenc", "REFERENCES", ["REFERENCES"]),
("mention", "REFERENCES", ["REFERENCES"]),
("discuss", "REFERENCES", ["REFERENCES"]),
("cite", "REFERENCES", ["REFERENCES"]),
```

### Phase 1d — Normalize Names Before MERGE

**File**: `src/knowledge_graph/ingest.py`, function `ingest_wiki_page` (lines 284-311)

Add a `_normalize_node_name` function and use it in all `MERGE` operations:

```python
def _normalize_node_name(name: str) -> str:
    """Normalize a node name for deduplication: lowercase, collapse whitespace, strip."""
    if not name:
        return name
    return " ".join(name.lower().split())
```

Use `_normalize_node_name(title)` in the primary MERGE and `_normalize_node_name(target)` in the target MERGE.

### Phase 1e — Guard Target MERGE with Wiki File Check

**File**: `src/knowledge_graph/ingest.py`, function `ingest_wiki_page` (line 298-316)

Before creating a target node, check if the name resolves to a wiki page. If not, skip the node creation and relationship entirely (unless confidence is explicitly provided):

```python
# Only create target node if it corresponds to a wiki page or has a confidence override
if target and target != title:
    target_file = _resolve_target_wiki_file(target)
    if target_file is None:
        logger.debug(f"Skipping placeholder node for unresolvable target '{target}'")
        continue  # skip this target
    # ... rest of target node creation
```

### Phase 2 — Cleanup

1. Delete test pages: `wiki/entities/test-a.md`, `wiki/concepts/test-b.md`, and all test artifacts in `wiki/raw/drafts/`
2. Deduplicate existing Neo4j nodes (merge properties + relationships)
3. Delete orphaned placeholder nodes
4. Wipe and re-ingest

### Phase 3 — Wipe + Re-ingest

1. `MATCH (n) DETACH DELETE n`
2. `FLUSHDB` on Redis
3. Restart server with reconciliation

### Phase 4 — Monitoring

Add an `/audit/graph` endpoint:
- Total nodes vs placeholder nodes (target: <10% placeholder)
- `RELATED_TO` ratio (target: <50%)
- Duplicate name groups (target: 0)
- Label consistency (target: no Person on non-Entity pages)
