---
created: 2026-06-22
protected: true
related:
- local-first-llm
- agent-architecture
- knowledge-graph-schema
- api-design
- mcp-server
sources:
- PROJECT_SPEC-2026
tags:
- project
- technology
- stack
title: Technology Stack
updated: '2026-06-25'
---

# Technology Stack

## Layer-to-Technology Mapping

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI | Modern Python API framework |
| Agent Framework | Pydantic AI + pydantic-graph | Core agent orchestration |
| Complex Workflows | LangGraph | Sub-workflows with checkpointing, streaming, human-in-the-loop |
| MCP | FastMCP | Model Context Protocol server |
| Knowledge Graph | Neo4j | Entity-relationship graph |
| Spacetime Engine | Qiskit | Time simulation, dilation, closed timelike curves |
| Field Manipulator | CUDA-Q | Hybrid quantum-classical field manipulation |
| AI Navigator | PennyLane | Neural-field model, QML |
| Optimization | D-Wave | Quantum annealing for path finding |
| Precision | IonQ | Trapped-ion precision computation |
| Config | Pydantic Settings | Type-safe configuration |
| Cache | Redis | In-memory caching |
| Batching | Celery/Ray | Distributed task processing |
| Observability | OpenTelemetry | Logs, metrics, traces |
| Testing | pytest | Unit, integration, and benchmark tests |
| Build | pyproject.toml | Python project configuration |
| Container | Docker + docker-compose | Containerization and orchestration |
| CI/CD | GitHub Actions | Automated testing and deployment |

## Agent Framework Detail

- **pydantic-graph** — Core agent orchestration with type-safety
- **LangGraph** — Complex sub-workflows with checkpointing, streaming, human-in-the-loop
- **Two-framework complexity** — Clear boundaries: pydantic-graph for agents, LangGraph for workflows

## See Also

- [[agent-architecture]]
- [[local-first-llm]]
- [[knowledge-graph-schema]]
- [[api-design]]
- [[mcp-server]]
- [[production-readiness]]

