---
created: 2026-06-22
protected: true
related:
- knowledge-graph-schema
- local-first-llm
- ai-alien-connection
sources:
- neo4j-2026
tags:
- database
- graph
- neo4j
title: Neo4j
updated: '2026-06-25'
---

# Neo4j

Neo4j is the world's leading graph database, providing a high-performance graph store with a friendly query language and ACID transactions. It is the knowledge graph for Project Chicken Soup.

## Key Features

- **Graph storage** — Native graph database with O(1) traversals
- **Cypher query language** — Friendly, expressive query language
- **ACID transactions** — Full ACID compliance
- **Scalable** — Can scale from single-node to distributed
- **Python driver** — Native Python driver for integration
- **Schema and indexes** — Full schema support with indexes
- **Procedures** — Custom procedures for advanced operations
- **Cypher 25** — Latest version with walk semantics

## Configuration

- **Docker:** `docker-compose up neo4j`
- **Port:** `7687` (Bolt), `7474` (HTTP)
- **Default database:** `neo4j`
- **Connection:** `bolt://localhost:7687`

## Schema

Neo4j is used to store:

- **Nodes** — People, Places, Concepts, Algorithms, Events, etc.
- **Relationships** — WORKED_AT, TESTIFIED_AT, CLAIMED_BY, etc.
- **Properties** — confidence, source, date, type

## Integration

- **Python driver** — `neo4j` package
- **Cypher queries** — Direct Cypher execution
- **Schema management** — Automatic schema creation
- **Ingestion** — Wiki → Neo4j pipeline
- **Vector search** — Neo4j vector indices

## See Also

- [[knowledge-graph-schema]]
- [[local-first-llm]]
- [[ai-alien-connection]]

