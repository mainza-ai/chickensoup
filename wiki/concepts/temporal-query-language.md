---
created: 2026-06-22
protected: true
related:
- temporal-reasoning-engine
- temporal-query-pipeline
- temporal-data-model
sources:
- PROJECT_SPEC-2026
tags:
- temporal
- query
- language
- quantum
title: Temporal Query Language
updated: '2026-06-25'
---

# Temporal Query Language

The Temporal Query Language is how you input information to the system. It defines the syntax, semantics, and types of queries supported.

## The Purpose

The Temporal Query Language allows users to ask the system questions about:

- **Timelines** — when did something happen? what's the temporal sequence?
- **Destinations** — where is something? what's the spatial relationship?
- **Paths** — what's the optimal path through spacetime?
- **Evidence** — what supports each claim?
- **Causality** — what caused what?

## The Syntax

The Temporal Query Language has the following syntax:

```
<TIMELINE QUERY>
  SELECT <entity>
  WHERE <condition>
  FROM <time_range>
  ORDER BY <property>

<TIME TRAVEL QUERY>
  FIND PATH
  FROM <start_time> TO <end_time>
  WHERE <criteria>
  OPTIMIZE FOR <metric>

<EVIDENCE QUERY>
  GET EVIDENCE
  FOR <claim>
  WITH <confidence_threshold>

<CAUSAL QUERY>
  FIND CAUSES
  OF <event>
  WITHIN <time_range>

<ANOMALY QUERY>
  DETECT ANOMALIES
  IN <time_range>
  ABOVE <threshold>
```

## The Semantics

The Temporal Query Language has the following semantics:

- **SELECT** — selects entities that match the query
- **WHERE** — filters entities by condition
- **FROM** — specifies the time range
- **ORDER BY** — orders the results by property
- **FIND PATH** — finds the optimal path through spacetime
- **OPTIMIZE FOR** — optimizes the path by metric (time, energy, credibility)
- **GET EVIDENCE** — gets evidence for a claim
- **WITH** — specifies the confidence threshold
- **FIND CAUSES** — finds the causes of an event
- **WITHIN** — specifies the time range
- **DETECT ANOMALIES** — detects anomalies in the temporal data
- **ABOVE** — specifies the threshold

## The Types of Queries

### Timeline Queries
```
SELECT UFOs
WHERE location = "Area 51"
FROM 1947 TO 2023
ORDER BY date
```

### Time Travel Queries
```
FIND PATH
FROM 1947 TO 2023
WHERE field_configuration = "optimal"
OPTIMIZE FOR time
```

### Evidence Queries
```
GET EVIDENCE
FOR "Bob Lazar worked at S-4"
WITH 0.8
```

### Causal Queries
```
FIND CAUSES
OF "Roswell crash"
WITHIN 1947-1950
```

### Anomaly Queries
```
DETECT ANOMALIES
IN 1947-2023
ABOVE 2.0
```

## The Connection to the Knowledge Graph

The Temporal Query Language queries the knowledge graph to:

- **Find entities** — search for entities that match the query
- **Find relationships** — search for relationships between entities
- **Find properties** — search for properties of entities
- **Find temporal positions** — search for temporal positions of entities

## The Connection to the Quantum Algorithms

The Temporal Query Language uses quantum algorithms to:

- **Find optimal paths** — use QAOA to find the optimal path through spacetime
- **Find optimal destinations** — use VQE to find the optimal destination
- **Find optimal evidence** — use quantum counting to find the optimal evidence
- **Find optimal causes** — use quantum walk search to find the optimal causes

## See Also

- [[temporal-reasoning-engine]]
- [[temporal-query-pipeline]]
- [[temporal-data-model]]

