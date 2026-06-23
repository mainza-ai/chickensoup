---
title: "Temporal Query Pipeline"
tags: [temporal, query, pipeline, quantum]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [temporal-reasoning-engine, temporal-query-language, agent-architecture]
---

# Temporal Query Pipeline

The Temporal Query Pipeline is the flow of information through the system. It defines how a query is processed from input to output.

## The Pipeline

The Temporal Query Pipeline has the following flow:

```
User Input → Query Agent → Research Agent → Navigation Agent → Orchestrator Agent → User Output
```

## The Agents

### Query Agent
Receives user queries, determines intent, routes to appropriate sub-agent.

- **Input** — user query (natural language or structured)
- **Output** — query type (timeline, path, evidence, causal)
- **Processing** — uses LLM to determine intent

### Research Agent
Explores the knowledge graph for evidence, credibility, and related claims.

- **Input** — query type
- **Output** — evidence, credibility scores, related claims
- **Processing** — uses Neo4j to query the knowledge graph

### Navigation Agent
Runs the AI Navigator (PennyLane) to compute optimal paths through spacetime.

- **Input** — start and end points
- **Output** — optimal path
- **Processing** — uses QAOA/VQE to find the optimal path

### Orchestrator Agent
Coordinates the flow: query → research → navigation → answer.

- **Input** — results from Research Agent and Navigation Agent
- **Output** — final answer
- **Processing** — fuses results, ranks by confidence

## The Steps

### Step 1: Query
The user submits a query through the API (`POST /query`).

### Step 2: Intent Detection
The Query Agent determines the intent of the query (timeline, path, evidence, causal).

### Step 3: Research
The Research Agent explores the knowledge graph for evidence, credibility, and related claims.

### Step 4: Navigation
The Navigation Agent runs the AI Navigator (PennyLane) to compute optimal paths through spacetime.

### Step 5: Fusion
The Orchestrator Agent fuses the results from Research Agent and Navigation Agent.

### Step 6: Output
The Orchestrator Agent returns the final answer to the user.

## The API

The Temporal Query Pipeline uses the following API endpoints:

- **POST /query** — submit a query, get AI interpretation
- **POST /navigate** — compute optimal time travel path
- **GET /graph/{entity}** — retrieve entity and related data
- **GET /status** — system health (LLM, Neo4j, quantum backends)
- **GET /models** — list available LLM models
- **POST /ingest** — ingest new wiki content into knowledge graph

## The Connection to Quantum Algorithms

The Temporal Query Pipeline uses quantum algorithms to:

- **Find optimal paths** — use QAOA to find the optimal path through spacetime
- **Find optimal destinations** — use VQE to find the optimal destination
- **Find optimal evidence** — use quantum counting to find the optimal evidence
- **Find optimal causes** — use quantum walk search to find the optimal causes

## See Also

- [[temporal-reasoning-engine]]
- [[temporal-query-language]]
- [[agent-architecture]]
