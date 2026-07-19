---
title: "Pulse Agent"
tags: [agent, living-almanac, last30days, pulse, budget]
created: 2026-07-12
updated: 2026-07-18
sources: [living-almanac]
related: [agent-architecture, budget-tracking, credibility-scoring, api-design, frontend-settings-menu]
---

# Pulse Agent

Entity-scoped ingestion that pulls fresh evidence for a wiki entity via the `last30days` engine, normalizes into `ClaimEvidence`, and hands off to quantum credibility layer. Never writes directly to entity/concept pages — `wiki/raw/pulse/` only.

## Class Shape

```python
class PulseAgent:
    def run_pulse(self, entity_name: str, handles: dict | None = None) -> PulseResult:
```

### Evidence Pipeline (execution order)

1. **Entity sanitization** — reject null bytes, newlines, cap 200 chars
2. **Wiki frontmatter read** — extract handles, tags, org flag
3. **Disabled gate** — `LAST30DAYS_ENABLED=false` returns clean no-op
4. **Budget check** via `ResourceLedger` (Lua atomic) — refusal logged
5. **Binary resolution** — `LAST30DAYS_BINARY_PATH` → cloned script → `npx last30days` → `last30days`
6. **Subprocess execution** with `TERM=dumb` (was `NO_COLOR=1`, changed to avoid breaking DuckDuckGo search)
7. **CLI timeout** — `LAST30DAYS_PULSE_TIMEOUT_SECONDS` (300s). On timeout: `proc.kill()` + `record_pulse_completed()` to prevent zombie accumulation.
8. **Parse via `last30days_adapter.py`** — JSON first (`ranked_candidates`/`claims`/`evidence`/`results`/`findings`), markdown fallback
9. **Rule-based filters** (in order):
   - Semantic disambiguation: word-boundary token matching, ≥60% of entity words must appear in claim
   - Noise floor: single-word entities require `engagement_count ≥ 5`
   - Hiring/jobs filter: blocks `jobs-web`, `jobs`, `careers` platforms + hiring keywords for non-org entities
10. **LLM relevance gate** (NEW): batches all evidence into a single LLM call, classifies each as RELEVANT/IRRELEVANT to the entity. Catches multi-meaning entity names ("Element 115" the company vs the element), Reddit boilerplate, cross-topic claims. Graceful degradation on LLM failure.
11. **DDGS fallback** (NEW): when CLI returns no evidence, queries DuckDuckGo directly via `ddgs` package. Results go through the same rule + LLM filter pipeline.
12. **Engagement normalization** — log-scaled, decayed with half-life 7d
13. **Max claims cap** — `LAST30DAYS_MAX_CLAIMS_PER_PULSE` (50)
14. **Write immutable snapshot** — `wiki/raw/pulse/{slug}-{date}-{time}.json+.md` (timestamped to prevent overwrites)
15. **Record spend**, append to log.md, return `PulseResult`

## Rule-Based Filter Details

### Semantic Disambiguation (`_apply_rule_filter`)

```python
ent_words = tokens from entity name, filtered to words > 2 chars, stop words removed
claim_tokens = word-boundary tokens (\b) from claim text + URL
match_count = count of ent_words appearing in claim_tokens
min_required = max(1, ceil(len(ent_words) * 0.6))
# Reject if match_count < min_required
```

Word-boundary matching prevents false positives ("element" in "elemental"). The 60% threshold allows some word variation while still requiring majority coverage.

### Hiring/Jobs Filter

Blocks evidence from `jobs-web`, `jobs`, or `careers` platforms for non-org entities. Also blocks hiring keywords (`hiring`, `careers`, `database engineer`, etc.) and known hiring domains (`greenhouse.io`, `ashbyhq.com`, `lever.co`, `workable.com`).

### Single-Word Noise Floor

Entities with names ≤1 word (e.g., "UFO", "UAP") require `engagement_count ≥ 5` to prevent noisy matches.

## LLM Relevance Filter (`_apply_llm_relevance_filter`)

```python
def _apply_llm_relevance_filter(self, evidence, entity_name, slug):
    # Batch all evidence into a single LLM prompt
    # Classify each as RELEVANT or IRRELEVANT to the entity
    # Only keep RELEVANT items
    # Graceful: on LLM failure, return all evidence unchanged
```

Designed to catch cases that token-based filters cannot:
- Entity name shared with a company/product ("Element 115" the restaurant vs Moscovium)
- Boilerplate Reddit metadata containing entity keywords by accident
- Claims from a different domain that happen to mention entity words

Uses `LLMClient.query_sync()` with 15s timeout. Batches ALL evidence items for an entity into a single prompt to minimize LLM calls.

## DDGS Fallback

When the CLI returns no evidence, PulseAgent queries DuckDuckGo directly via the `ddgs` Python package (`ddgs>=9.14.4`). Results flow through the same filter pipeline (rule filters + LLM gate + engagement normalization). This provides a backup when the CLI's built-in DuckDuckGo client is rate-limited or unavailable.

## Cross-File Deduplication

`load_recent_pulse_evidence()` in `pulse_writer.py` deduplicates evidence across all pulse snapshot files:
- Key: `claim_text[:200]`
- Rule: keep the version with highest `engagement_count`
- This prevents the 147-file × 4-items = "545 evidence" inflation bug

## Security

- `shell=False` always — `run_pulse("Bob Lazar; rm -rf /")` passes malicious string as single arg, not executed
- `_sanitize_entity_name`: rejects `\x00`, `\n`, `\r`, caps 200 chars
- Subprocess timeout `LAST30DAYS_PULSE_TIMEOUT_SECONDS=300`
- Config `LAST30DAYS_BINARY_PATH` + `shutil.which` resolution
- Subprocess env uses `TERM=dumb` instead of `NO_COLOR=1` (NO_COLOR breaks DuckDuckGo search)

## Bug Fixes (July 2026)

| Bug | Cause | Fix |
|-----|-------|-----|
| Zombie accumulation | `proc.communicate(timeout=1)` loop deadlocked on pipe buffer | Replaced with `proc.wait(timeout=timeout)` + single `proc.communicate()` |
| 545 garbage evidence for Element 115 | 147 redundant snapshots × 4 garbage items, no dedup | Cross-file dedup by claim_text, "jobs" platform filter, LLM relevance gate |
| DDGS fallback had zero filters | Evidence created directly without any filtering | Rerouted through full rule + LLM filter pipeline |
| `NO_COLOR=1` broke search | Env var interfered with DuckDuckGo client | Changed to `TERM=dumb` |
| Timeout didn't record completion | Missing `record_pulse_completed()` in timeout handler | Added `proc.kill()` + `record_pulse_completed()` |

## Snapshot Format

- `wiki/raw/pulse/{slug}-{date}-{time}.json`: timestamped to prevent same-day overwrites (was `{slug}-{date}.json`)
- `wiki/raw/pulse/{slug}-{date}-{time}.md`: human-readable per-claim sections

## Endpoints

- `POST /pulse/{entity_name}` with `{"handles": {"x": "@handle", "subreddit": "r/ufos"}}` → `PulseResult`
- `GET /pulse/history?entity_name=&limit=50` → pulse history with evidence counts
- `GET /budget/status` → BudgetStatus
- `POST /budget/approve` → clear HOLD

## Acceptance

- `run_pulse("Bob Lazar")` with `ENABLED=false` returns no-op, not error
- With enabled, writes one immutable file to `wiki/raw/pulse/`, never touches `wiki/entities/`
- Budget ceiling checked before pull; subprocess never called when budget exceeded
- `shell=False` always (tested)
- Adapter handles both JSON and markdown output shapes
- Zero zombie processes after timeout (verified: `proc.kill()` called)
- Cross-file dedup prevents evidence inflation (verified: 147 snapshots → 5 unique claims)

## See Also

- [[budget-tracking]]
- [[credibility-scoring]]
- [[agent-architecture]]
- [[api-design]]
- [[frontend-settings-menu]]
- [[living-almanac-project]]
- [[pydantic-settings]]
