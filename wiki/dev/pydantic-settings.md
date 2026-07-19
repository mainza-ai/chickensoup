
## ALMANAC_TIER_1_ENTRIES

- **Type**: `str` (CSV of slugs)
- **Default**: Comma-separated list of 17 priority entities
- **Purpose**: Controls which entities the almanac processes on each generation cycle. Replaces old hardcoded 3-entity fallback.
- **Location**: `src/config.py:140`

## DDGS (DuckDuckGo Search) Dependency

- **Package**: `ddgs>=9.14.4` (in `pyproject.toml`)
- **Purpose**: Provides web search for the `last30days` CLI pulse agent. Replaces `NO_COLOR=1` env var workaround with `TERM=dumb` in subprocess environment to avoid breaking the search backend.
- **File**: `src/agents/pulse_agent.py:189` — subprocess env uses `TERM=dumb` instead of `NO_COLOR=1`

## DDGS (DuckDuckGo Search) Dependency

- **Package**: `ddgs>=9.14.4` (in `pyproject.toml`)
- **Purpose**: Provides web search for the `last30days` CLI pulse agent. Used as fallback when CLI's built-in DuckDuckGo client is unavailable.
- **Subprocess env**: `TERM=dumb` (was `NO_COLOR=1` — changed because NO_COLOR breaks DuckDuckGo search in the CLI)

## LAST30DAYS_PULSE_TIMEOUT_SECONDS

- **Type**: `int`
- **Default**: `300`
- **Purpose**: Maximum time in seconds to wait for a last30days CLI pulse before timing out. On timeout, the process is killed and `record_pulse_completed()` is called with 0 divergence.

## Pulse Agent Evidence Filters

All defined in `src/agents/pulse_agent.py`:
- `_apply_rule_filter()` — semantic disambiguation (60% word-boundary match), hiring platform block (`jobs-web`, `jobs`, `careers`), engagement noise floor
- `_apply_llm_relevance_filter()` — LLM-based relevance classification (batch per entity). Graceful degradation.
- Cross-file dedup in `load_recent_pulse_evidence()` — `claim_text[:200]` key, highest engagement wins
