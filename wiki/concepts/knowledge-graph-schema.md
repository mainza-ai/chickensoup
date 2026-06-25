---
title: "Knowledge Graph Schema"
tags: [knowledge-graph, schema, neo4j]
created: 2026-06-22
updated: 2026-06-22
sources: [neo4j-2026]
related: [neo4j, local-first-llm, ai-alien-connection]
---

# Knowledge Graph Schema

The knowledge graph schema for Project Chicken Soup defines the nodes, relationships, and properties used to represent UFO/Alien/Time Travel lore.

## Nodes

### Person
- **Properties:** name, description, source, date, confidence
- **Examples:** David Grusch, Bob Lazar

### Place
- **Properties:** name, description, location, source, date, confidence
- **Examples:** Area 51, S-4, Roswell

### Concept
- **Properties:** name, description, source, date, confidence
- **Examples:** time-travel, field-manipulation, entanglement

### QuantumPlatform
- **Properties:** name, description, type, source, date, confidence
- **Examples:** Qiskit, CUDA-Q, PennyLane

### Algorithm
- **Properties:** name, description, complexity, source, date, confidence
- **Examples:** QFT, QPE, QAOA, VQE

### Event
- **Properties:** name, description, date, source, confidence
- **Examples:** UAP hearings, Roswell crash

### Object
- **Properties:** name, description, source, date, confidence
- **Examples:** Element 115, the thing

### Project
- **Properties:** name, description, source, date, confidence
- **Examples:** Project SERPO

### Entity
- **Properties:** name, description, source, date, confidence
- **Examples:** Earth, UFOs, UAPs

### Paper
- **Properties:** title, authors, year, source, confidence
- **Examples:** Babbush et al. (2023), Knuth et al. (2025)

## Relationships

- **WORKED_AT** — Person worked at Place
- **TESTIFIED_AT** — Person testified at Event
- **CLAIMED_BY** — Entity claimed by Person
- **PART_OF** — Entity is part of Entity
- **USES** — Entity uses Entity
- **IMPLEMENTS** — Entity implements Entity
- **RELATED_TO** — Entity is related to Entity (bidirectional)
- **HAS_PROPERTY** — Entity has property
- **CONNECTED_TO** — Entity is connected to Entity
- **ORCHESTRATES** — Agent orchestrates Agent
- **CITES** — Paper cites Entity

## Properties

- **confidence** — Credibility score (0-1)
- **source** — Origin (Grusch-2023, Lazar-1989, etc.)
- **date** — Date when claim was made
- **type** — Type of entity (LLM, VLM, Embedding, etc.)

## See Also

- [[neo4j]]
- [[local-first-llm]]
- [[ai-alien-connection]]
