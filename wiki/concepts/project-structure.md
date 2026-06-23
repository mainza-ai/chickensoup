---
title: "Project Structure"
tags: [project, structure, organization]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [agent-architecture, technology-stack, api-design, mcp-server, knowledge-graph-schema]
---

# Project Structure

## Root Files

```
chickensoup/
├── AGENTS.md
├── PROJECT_SPEC.md
├── README.md
├── pyproject.toml
├── .python-version
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── papers/
├── wiki/
├── src/
├── tests/
└── notebooks/
```

## Source Directory

```
src/
├── main.py                 # Entry point
├── config.py               # Configuration (Pydantic Settings)
├── discovery.py            # LLM auto-discovery
├── models.py               # Core Pydantic models
├── api/                    # FastAPI routes
│   ├── query.py            # POST /query
│   ├── graph.py            # GET /graph/{entity}
│   ├── navigate.py         # POST /navigate
│   ├── status.py           # GET /status
│   ├── models.py           # GET /models
│   └── ingest.py           # POST /ingest
├── mcp/                    # MCP server
│   └── server.py           # FastMCP server with tools
├── agents/                 # Agent framework
│   ├── query_agent.py      # Query Agent (pydantic-graph)
│   ├── research_agent.py   # Research Agent (pydantic-graph)
│   ├── navigation_agent.py # Navigation Agent (pydantic-graph)
│   └── orchestrator.py     # Orchestrator Agent (pydantic-graph)
├── langgraph_workflows/    # LangGraph sub-workflows
│   ├── research_workflow.py
│   ├── navigation_workflow.py
│   └── evaluation_workflow.py
├── knowledge_graph/        # Neo4j integration
│   ├── schema.py           # Graph schema
│   ├── queries.py          # Cypher queries
│   └── ingestion.py        # Graph ingestion from wiki
├── spacetime_engine/       # Qiskit
│   ├── engine.py           # Spacetime simulation
│   ├── dilation.py         # Time dilation calculation
│   └── curves.py           # Closed timelike curves
├── field_manipulator/      # CUDA-Q
│   ├── manipulator.py      # Field manipulation
│   ├── bubble.py           # Bubble creation
│   └── circuits.py         # Quantum circuits
├── ai_navigator/           # PennyLane
│   ├── navigator.py        # AI Navigator
│   ├── neural_field.py     # Neural field model
│   └── qml.py              # Quantum ML
├── llm/                    # LLM layer
│   ├── client.py           # LLM client
│   ├── omlx.py             # oMLX connection
│   ├── ollama.py           # Ollama connection
│   └── lm_studio.py        # LM Studio connection
├── cache/                  # Redis caching
│   ├── cache.py            # Cache implementation
│   └── policies.py         # Cache policies
└── utils/                  # Utilities
    ├── logging.py          # Logging setup
    └── telemetry.py        # OpenTelemetry
```

## Tests

```
tests/
├── test_api.py
├── test_agents.py
├── test_graph.py
├── test_llm.py
└── test_qc.py
```

## Notebooks

```
notebooks/
├── spacetime_simulation.ipynb
├── field_manipulation.ipynb
└── ai_navigator.ipynb
```

## See Also

- [[technology-stack]]
- [[agent-architecture]]
- [[api-design]]
- [[mcp-server]]
- [[knowledge-graph-schema]]
