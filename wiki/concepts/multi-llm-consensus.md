---
created: 2026-06-23
protected: true
related:
- llm-fallback-chain
- llm-discovery
- api-design
- local-first-llm
sources: []
tags:
- llm
- consensus
- multi-llm
- reliability
title: Multi-LLM Consensus
updated: '2026-06-25'
---

# Multi-LLM Consensus

## Purpose

The Multi-LLM Consensus system queries multiple LLM models across different providers and computes semantic agreement. This provides more reliable answers by cross-referencing independent model outputs.

## Implementation

Located in `src/multi_llm.py`. The `MultiLLMConsensus` class:

1. Discovers all available providers (via `discover_active_provider`)
2. Queries each provider with the same prompt
3. Computes pairwise semantic similarity using Jaccard word overlap
4. Returns the most representative response + agreement score

```
User Query → Discover Providers → Query All → Compare Similarity → Return Consensus
```

## Similarity Scoring

Consensus uses word-level Jaccard similarity between response pairs. The average pairwise similarity becomes the confidence score:

$$
\text{score} = \frac{1}{n} \sum_{i < j} \frac{|R_i \cap R_j|}{|R_i \cup R_j|}
$$

## API Endpoint

**POST** `/consensus/query` — Submit a query for consensus evaluation across all active providers.

## Fallback

When no real LLMs are available, `_generate_mocked_consensus` produces reasonable mock responses based on the query's topic, ensuring the system remains functional offline.

## See Also

- [[llm-fallback-chain]]
- [[llm-discovery]]
- [[local-first-llm]]
- [[api-design]]

