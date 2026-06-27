---
title: "Knowledge Graph Ingestion"
tags: [knowledge-graph, neo4j, ingestion, cypher]
created: 2026-06-26
updated: 2026-06-26
sources: [knowledge-graph-ingest]
related: [neo4j, knowledge-graph-schema, wiki-file-system, ingestion-pipeline, langgraph-features]
---

# Knowledge Graph Ingestion

The knowledge graph ingestion pipeline converts wiki markdown pages into Neo4j nodes and relationships. Implementation in `src/knowledge_graph/ingest.py` (299 lines).

## Overview

Ingestion runs in two phases:
1. **Deterministic** — YAML frontmatter parsed for tags, sources, related entities. `[[wikiname]]` links in body text become `RELATED_TO` edges.
2. **LLM enrichment** — The active LLM classifies relationship types between nodes using a schema-constrained prompt.

This makes the graph functional immediately (Phase 1) and gradually improves it (Phase 2).

## Schema Constraints

### Valid Neo4j Labels

```python
VALID_LABELS = frozenset({
    "Person", "Place", "Concept", "Object", "Project",
    "Event", "Entity", "Paper", "QuantumPlatform", "Algorithm"
})
```

Invalid labels are sanitized to `Entity`.

### Relationship Type Matrix

The ingestion engine enforces a strict relationship type matrix. Only semantically valid edge types are allowed between label pairs:

| From → To | Valid Relationship Types | Default |
|-----------|-------------------------|---------|
| Person → Place | VISITED, BORN_IN, LOCATED_AT, TESTIFIED_AT | LOCATED_AT |
| Person → Project | MEMBER_OF, LEAD_ON, CONTRIBUTED_TO, FOUNDED | CONTRIBUTED_TO |
| Person → Concept | PROPOSED, RESEARCHED, CRITICIZED, SUPPORTED | RESEARCHED |
| Person → Organization | EMPLOYED_BY, FOUNDED, CONSULTED_FOR, MEMBER_OF | EMPLOYED_BY |
| Person → Event | WITNESSED, PARTICIPATED_IN, DISCLOSED | PARTICIPATED_IN |
| Project → Concept | IMPLEMENTS, BASED_ON, TESTS | BASED_ON |
| Project → Object | USES, MANUFACTURES, REVERSE_ENGINEERS | USES |
| Concept → Concept | EXTENDS, CONTRADICTS, EQUIVALENT_TO, INFLUENCED | INFLUENCED |
| Event → Place | OCCURRED_AT, INVESTIGATED_IN | OCCURRED_AT |
| Event → Person | INVOLVED, WITNESSED_BY, CLAIMED_BY | INVOLVED |

## Ingestion Flow

```
Markdown Page
     │
     ▼
parse_markdown_frontmatter() → {tags, sources, related}
     │
     ▼
infer_node_label() → Primary label (Person/Place/Concept/...)
     │
     ▼
MERGE primary node (name, tags, sources, content_preview)
     │
     ▼
For each target (related + [[wikiname]] links):
  │  MERGE target node
  │  _query_llm_for_edge_type() → (rel_type, should_reverse)
  │  MERGE (source)-[rel_type]->(target)
  │
  ▼
(nodes_created, rels_created)
```

## Primary Node Label Inference

Tags are mapped to Neo4j labels via a category map:

| Tag | Neo4j Label |
|-----|-------------|
| person, whistleblower, scientist, researcher, witness, military, agent | Person |
| place, location, area, country, city | Place |
| event, crash, incident, encounter, sighting, accident, recovery, landing | Event |
| concept, theory, idea, principle, model, framework | Concept |
| project, program, experiment, mission, operation | Project |
| object, craft, artifact, device, technology, weapon, material, element | Object |

When no tag matches, the label is inferred from the wiki directory structure: `entities/` → Entity, `concepts/` → Concept, `projects/` → Project.

## LLM Edge Classification

`_query_llm_for_edge_type()` probes the active LLM to determine the best relationship type between a source and target node.

### Schema-Constrained Prompt

The LLM receives:
- Source node name and label
- Target node name and label
- Context (first 500 chars of body text)
- **Only valid relationship types** from the schema matrix

The LLM returns a JSON object with a single `relationship` field. If the response is invalid, the default type for that label pair is used.

### Keyword Heuristic Fallback

When no LLM is available (simulated provider or no models), keyword heuristics constrained by the schema matrix determine edge types:

| Keywords | Relationship Type |
|----------|-------------------|
| "worked", "employed", "researcher" | EMPLOYED_BY / WORKED_AT |
| "testified", "testimony" | TESTIFIED_AT |
| "proposed", "developed", "formulated" | PROPOSED |
| "implements", "realizes" | IMPLEMENTS |
| "uses", "utilizes" | USES |
| "occurred", "crashed", "landed" | OCCURRED_AT |

### Direction Reversal

If the target-to-source direction fits the schema matrix but source-to-target does not, the direction is reversed. For example, if `("Person", "Place")` has valid types but `("Place", "Person")` does not, the edge is drawn as `Place → Person` with the appropriate relationship type.

## API Endpoint

`POST /ingest/bulk` — Clears Neo4j and re-ingests all wiki pages.

```
For each .md file in wiki/entities/, wiki/concepts/, wiki/projects/:
  1. Read file content
  2. ingest_wiki_page(driver, title, content, tags, sources)
  3. Accumulate nodes_created, rels_created
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `WIKI_DATA_DIR` | `wiki` | Wiki root directory |
| `LLM_ACTIVE_PROVIDER` | (auto-discovered) | Provider for edge classification |
| `LLM_ACTIVE_MODEL` | (auto-discovered) | Model for edge classification |

## See Also

- [[knowledge-graph-schema]] — Neo4j node types and relationships
- [[wiki-file-system]] — Markdown page format
- [[ingestion-pipeline]] — File/folder upload pipeline
- [[chat-to-wiki-pipeline]] — Chat-to-wiki conversion
- [[neo4j]] — Neo4j database
