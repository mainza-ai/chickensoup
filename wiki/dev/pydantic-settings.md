
## ALMANAC_TIER_1_ENTRIES

- **Type**: `str` (CSV of slugs)
- **Default**: Comma-separated list of 17 priority entities
- **Purpose**: Controls which entities the almanac processes on each generation cycle. Replaces old hardcoded 3-entity fallback.
- **Location**: `src/config.py:140`

## DDGS (DuckDuckGo Search) Dependency

- **Package**: `ddgs>=9.14.4` (in `pyproject.toml`)
- **Purpose**: Provides web search for the `last30days` CLI pulse agent. Replaces `NO_COLOR=1` env var workaround with `TERM=dumb` in subprocess environment to avoid breaking the search backend.
- **File**: `src/agents/pulse_agent.py:189` — subprocess env uses `TERM=dumb` instead of `NO_COLOR=1`
