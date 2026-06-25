---
created: 2026-06-22
protected: true
related:
- fastmcp
- local-first-llm
- agent-architecture
- field-geometry-tensor
sources:
- fastmcp-2026
tags:
- mcp
- fastmcp
- tools
title: MCP Server
updated: '2026-06-25'
---

# MCP Server

The MCP (Model Context Protocol) server for Project Chicken Soup exposes tools for external consumers: LLM agents, web apps, and desktop apps. It runs alongside the FastAPI server and uses the same service layer.

## Tools

### 1. `simulate_spacetime`

Run a spacetime simulation with configurable parameters.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_time` | string (ISO 8601) | Yes | — | Target spacetime coordinate |
| `grid_resolution` | int | No | 32 | Grid points per dimension |
| `fidelity_mode` | enum | No | "medium" | light / medium / heavy |
| `mass_distribution` | object | No | {} | Mass-energy distribution (source terms) |
| `perturbation_params` | object | No | {} | Field manipulation parameters |

**Response:**
```json
{
  "tensor": {
    "shape": [32, 32, 32, 1],
    "lapse_shape": [32, 32, 32, 1],
    "shift_shape": [32, 32, 32, 1, 3],
    "metric_3d_shape": [32, 32, 32, 1, 3, 3],
    "size_bytes": 294912,
    "data": "<base64-compressed-numpy>"
  },
  "summary": {
    "mean_curvature": 0.042,
    "max_perturbation": 0.187,
    "valid_metric": true,
    "lorentzian_signature": true
  }
}
```

### 2. `analyze_field`

Run field manipulation analysis on a region of spacetime.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `region` | object | Yes | — | Bounding box { x_min, x_max, y_min, y_max, z_min, z_max } |
| `field_strength` | float | Yes | — | Magnitude of field manipulation |
| `frequency` | float | No | 7.46 | Operating frequency in Hz |

**Response:** Analysis results with field gradients, energy density, and stability metrics.

### 3. `find_paths`

Find optimal time travel paths between two spacetime points.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start` | object | Yes | — | Starting spacetime coordinates |
| `end` | object | Yes | — | Target spacetime coordinates |
| `num_paths` | int | No | 3 | Number of candidate paths |
| `cost_function` | string | No | "proper_time" | proper_time / energy / risk |
| `constraints` | object | No | {} | Path constraints |

**Response:**
```json
{
  "paths": [
    {
      "trajectory": [[x, y, z, t], ...],
      "proper_time": 42.0,
      "energy_cost": 1.2e9,
      "confidence": 0.87,
      "ctc_violation": false
    }
  ],
  "selected_path": 0
}
```

### 4. `query_graph`

Query the knowledge graph for entities and relationships.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity_name` | string | Yes | — | Name of the entity to query |
| `relationship_type` | string | No | null | Filter by edge type |
| `depth` | int | No | 1 | Number of hops (1-3) |
| `confidence_threshold` | float | No | 0.0 | Minimum confidence score |

**Response:** Entity details with related entities at specified depth.

### 5. `get_evidence`

Get evidence for a claim from the knowledge graph.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `claim` | string | Yes | — | The claim to find evidence for |
| `max_sources` | int | No | 5 | Maximum number of sources |

**Response:** Evidence items with confidence scores, sources, and timestamps.

### 6. `explore_concept`

Explore a concept and related claims with depth.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `concept` | string | Yes | — | Concept name |
| `depth` | string | No | "standard" | overview / standard / deep |

**Response:** Concept explanation with related entities, evidence, and confidence scores.

## Error Codes

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| 100 | Simulation failed (generic) | 500 |
| 101 | Metric tensor invalid (signature check failed) | 422 |
| 102 | Grid resolution exceeds limits | 422 |
| 200 | Query returned no results | 404 |
| 201 | All results below confidence threshold | 404 |
| 300 | Provider unavailable (quantum backend down) | 503 |
| 301 | Provider unavailable (LLM discovery failed) | 503 |

## Protocol

- **MCP version:** Latest supported by FastMCP
- **Client types:** LLM agents (via sampling), web apps (via HTTP), SwiftUI app (via HTTP)
- **Discovery:** Clients can list available tools via `GET /tools`
- **Auth:** Same as FastAPI (API key in header, or none for local-only)

## Integration

- **FastAPI:** MCP server registers routes alongside FastAPI (same port or separate)
- **Pydantic AI:** Agent tools call MCP tools through Pydantic AI's tool interface
- **SwiftUI:** The app calls MCP tools via HTTP from the backend service layer
- **LangGraph:** Workflow nodes can call MCP tools as external actions

## See Also

- [[fastmcp]] — The MCP implementation
- [[agent-architecture]] — How agents use MCP tools
- [[field-geometry-tensor]] — The data structure returned by simulate_spacetime
- [[api-design]] — REST API design

