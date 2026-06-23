---
title: "LangGraph Workflows"
tags: [langgraph, workflows, graph, orchestration]
created: 2026-06-22
updated: 2026-06-22
sources: [langgraph-2026]
related: [langgraph, agent-architecture, integration-architecture, knowledge-graph-schema]
---

# LangGraph Workflows

LangGraph handles **complex sub-workflows** that require checkpointing, human-in-the-loop, streaming, and persistence. These are the "heavy machinery" workflows beneath the pydantic-graph orchestration layer.

## Workflow Architecture

All workflows share a common pattern:

```
Input Node → Processing Nodes (parallel where possible) → Evaluation Node → Output Node
                                              ↓
                                    Conditional edge (eval → re-process or continue)
```

Each node is a typed Python function with a Pydantic state schema. Edges are conditional or direct. Checkpointing saves state at every superstep.

## Research Workflow

The Research Agent uses this workflow to explore the knowledge graph for evidence, credibility, and related claims.

### Graph Definition

```
UserQuery Node → Entity Extraction Node → Knowledge Graph Query Node → Evidence Evaluation Node → Context Assembly Node → Result
                                         ↓                           ↓
                                    Conditional: low confidence → Re-query Node → KG Query (retry)
```

### Node State Schema

```python
class ResearchState(BaseModel):
    query: str
    entities: list[str] = []
    relationships: list[Relationship] = []
    evidence: list[Evidence] = []
    confidence: float = 0.0
    iteration: int = 0
    errors: list[str] = []
```

### Node Details

| Node | Input | Output | Description |
|------|-------|--------|-------------|
| **UserQuery** | Raw query string | Parsed query with intent | Splits query into entities and relationship types |
| **EntityExtraction** | Parsed query | List of entity names | Uses LLM + regex to extract entity mentions from query |
| **KnowledgeGraphQuery** | Entity names | Matching nodes and edges | Generates Cypher query, executes against Neo4j |
| **EvidenceEvaluation** | Raw graph results | Scored evidence list | Evaluates each result: confidence, source recency, corroboration |
| **ContextAssembly** | Scored evidence | Formatted context string | Ranks evidence by score, formats for LLM prompt |
| **Re-query** | Low-confidence results | Refined query | Reformulates KG query with broader or narrower terms |

### Conditional Edges
- `evidence_confidence < 0.3` AND `iteration < 3`: → Re-query Node
- `evidence_confidence >= 0.3` OR `iteration >= 3`: → ContextAssembly Node

### Error Handling
- KG Query failure: retry 3x with exponential backoff (1s, 4s, 16s)
- All retries exhausted: circuit breaker opens (5 failures in 60s window)
- Circuit breaker open: bypass KG, return cached or empty results
- Entity Extraction LLM failure: fall back to regex-only extraction

### Human-in-the-Loop
- If `confidence` is between 0.3 and 0.6 after all iterations: pause workflow, prompt human to review evidence
- Human can: approve, reject, or modify evidence before continuing

## Navigation Workflow

The Navigation Agent uses this workflow to compute optimal paths through spacetime.

### Graph Definition

```
Path Request → Metric Load Node → Path Proposer Node → Path Evaluation Node → Optimization Node → Path Selection Node → Result
                                                                                                            ↓
                                                                                                Conditional: stale metric → Re-fetch
```

### Node State Schema

```python
class NavigationState(BaseModel):
    start_coords: SpacetimePoint
    end_coords: SpacetimePoint
    metric_tensor: FieldGeometryTensor | None = None
    candidate_paths: list[Path] = []
    best_path: Path | None = None
    cost_function: Callable = geodesic_deviation
    iteration: int = 0
    metric_timestamp: datetime | None = None
```

### Node Details

| Node | Input | Output | Description |
|------|-------|--------|-------------|
| **PathRequest** | Start/end coords + constraints | Validated navigation parameters | Validates coords are within simulation domain |
| **MetricLoad** | Navigation parameters | FieldGeometryTensor | Loads latest tensor from backend (or cache) |
| **PathProposer** | Tensor | Multiple candidate paths | Geodesic integration from multiple initial conditions |
| **PathEvaluation** | Candidate paths + tensor | Scored paths | Evaluates each path: proper time, energy, feasibility, risk |
| **Optimization** | Scored paths + tensor | Optimized path | PennyLane QML refinement on best candidates |
| **PathSelection** | Optimized paths | Final path | Selects path with best cost function |

### Conditional Edges
- `metric_timestamp` older than 30 minutes: → re-fetch Metric (stale metric flag)
- Cost function delta > 10% between iteration 1 and iteration N: → further optimization (incomplete convergence flag)

### Error Handling
- Metric load fails: retry 2x, then use cached metric with staleness warning in response
- Optimization diverges: clamp to best classical geodesic, flag warning
- No valid paths found: return empty with reason (metric too perturbed? constraints too tight?)

### Checkpointing
State is saved at every superstep. If the workflow crashes, it can resume from the last checkpoint. Checkpoints expire after 24 hours.

## Evaluation Workflow

The Evaluation Workflow runs benchmarks (see [[evaluation-framework]]) and produces reports.

### Graph Definition

```
Eval Request → Test Case Load Node → Layer Test Node → Comparison Node → Report Generation Node → Result
                                              ↓
                                    Conditional: all tests? → next test or report
```

### Node State Schema

```python
class EvalState(BaseModel):
    test_suite: str = "light"
    test_cases: list[TestCase] = []
    current_test_index: int = 0
    results: dict[str, TestResult] = {}
    report: EvalReport | None = None
    pass_fail: dict[str, str] = {}
```

### Node Details

| Node | Input | Output | Description |
|------|-------|--------|-------------|
| **EvalRequest** | Test suite name (light/medium/heavy) | Test case list | Loads the appropriate benchmark suite |
| **TestLoad** | Test case list | Individual test case | Iterates through test cases |
| **LayerTest** | Single test case | Raw result | Runs the relevant layer against the test case |
| **Comparison** | Raw result + expected | Deviation scores | Compares result to analytic solution |
| **Report** | All deviation scores | Report | Generates pass/fail/warning report |

### Conditional Edges
- `current_test_index < len(test_cases)`: → TestLoad (next test)
- `current_test_index >= len(test_cases)`: → ReportGeneration

### Error Handling
- Individual test failure: log error, mark test as FAIL, continue with next test
- Layer crash on test: retry once, then mark as ERROR and continue
- All tests in a layer fail: abort workflow, return partial report with ERROR status

## Workflow Configuration

```yaml
workflows:
  research:
    checkpoint: true
    max_iterations: 3
    timeout: 120s
    retry_policy: exponential_backoff(1, 4, 16)
    circuit_breaker: { failures: 5, window: 60s }
  navigation:
    checkpoint: true
    max_iterations: 5
    timeout: 300s
    metric_ttl: 30m
  evaluation:
    checkpoint: true
    timeout: 600s
    parallel_tests: true
```

## See Also

- [[agent-architecture]] — How LangGraph fits into the multi-agent system
- [[integration-architecture]] — How workflows connect to other subsystems
- [[evaluation-framework]] — What the evaluation workflow tests
- [[field-geometry-tensor]] — The data structure flowing through navigation workflows
- [[knowledge-graph-schema]] — The graph the research workflow queries
