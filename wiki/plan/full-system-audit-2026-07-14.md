---
title: "Full System Audit — Neo4j, Spacetime Timeline, Search/Responsiveness"
tags: [audit, neo4j, data-quality, timeline, search, responsiveness, real-time]
created: 2026-07-14
updated: 2026-07-14
sources: [neo4j-audit-2026-07-14, codebase-scan-2026-07-14]
related: [neo4j-data-quality-remediation, knowledge-graph-schema, temporal-data-model, temporal-query-pipeline, real-time-progress-visibility]
---

# Full System Audit — Neo4j, Spacetime Timeline, Search/Responsiveness

Date: 2026-07-14
Scope: Neo4j graph data quality, spacetime timeline population accuracy, search and application responsiveness

---

## Part 1: Neo4j Graph Audit

### 1.1 Current Graph Statistics

| Metric | Value |
|---|---|
| Total nodes | 560 |
| Total relationships | 4,588 |
| Unique node labels | 10 registered, 7 in use |
| Unique relationship types | 50 defined, ~20 in use |
| Orphan nodes (no relationships) | 1 (`microsoft q#`) |
| Duplicate names (lowercase normalization) | 0 |

### 1.2 Node Label Distribution

| Label | Count | Status |
|---|---|---|
| Entity (base) | 560 | All nodes |
| Person | 234 | Heavy — includes many mislabeled wiki-link targets |
| Project | 25 | Reasonable |
| Object | 13 | Reasonable |
| Event | 10 | Underpopulated — many real events not labeled |
| Place | 6 | Severely underpopulated |
| Concept | 3 | Severely underpopulated — only 3 nodes |
| Algorithm | 0 | Registered but never assigned |
| Paper | 0 | Registered but never assigned |
| QuantumPlatform | 0 | Registered but never assigned |

**Gap 1.1: 3 labels have zero nodes.** `Algorithm`, `Paper`, and `QuantumPlatform` exist in `VALID_LABELS` and in the schema documentation, but no ingestion code path ever assigns them. The label inference function `_infer_primary_label` only scores against `[Concept, Person, Place, Event, Project, Object]`. Any wiki page whose content clearly describes a quantum algorithm or a scientific paper gets labeled as `Concept` or `Object` instead.

### 1.3 Relationship Distribution

| Relationship | Count | Notes |
|---|---|---|
| REFERENCES | 818 | Generic fallback — semantic signal lost |
| RELATED_TO | 706 | Generic fallback — semantic signal lost |
| EMPLOYED_BY | 57 | Mostly correct |
| CONTRIBUTED_TO | 43 | Reasonable |
| LOCATED_AT | 18 | Underpopulated |
| VISITED | 11 | Underpopulated |
| BORN_IN | 6 | Underpopulated |
| PARTICIPATED_IN | 3 | Underpopulated |
| WITNESSED | 2 | Underpopulated |
| TESTIFIED_AT | 1 | Underpopulated |
| All other types | 0 | Never created |

**Total generic (REFERENCES + RELATED_TO):** 1,524 of 4,588 = 33%

**Gap 1.2: 1/3 of all relationships are semantically meaningless.** `REFERENCES` and `RELATED_TO` carry no information about *how* two entities connect. The `_fallback_heuristic_edge_type` function has keyword matching that covers only ~30 keyword→relationship mappings, and the LLM edge classification was removed (now delegates directly to heuristics). 33 of 49 defined schema pairs are dominated by their `"default"` fallback.

**Gap 1.3: Many relationship types never fire.** Types like `CREATED`, `FOUNDED`, `DISCLOSED`, `CONTRADICTS`, `EQUIVALENT_TO`, `DEMONSTRATES`, `CAUSED`, `HOSTS`, `STORED_IN`, `PART_OF` have zero occurrences despite being defined in `SCHEMA_RELATIONSHIPS`. The heuristic keyword matcher doesn't include keywords for most of these.

### 1.4 Node Property Completeness

| Property | % Populated | Notes |
|---|---|---|
| `name` | 100% | Uniqueness constraint |
| `confidence` | 100% | |
| `display_name` | 99.5% | |
| `content_preview` | 85.5% | 81 nodes missing |
| `tags` | 85.5% | |
| `sources` | 85.5% | |
| `fallback` | 85.5% | |
| `protected` | 85.5% | |
| `date` | 0% | **Never written** — index is dead |
| `type` | 0% | **Never written** — index is dead |
| Slugs, summaries, aliases, etc. | 0% | Documented in schema, never populated |

**Gap 1.4: 81 nodes missing content_preview (14.5%).** These are largely placeholder/target nodes created via the wikilink MERGE path. The `_resolve_target_wiki_file` guard (Phase 1e) should reduce these, but existing ones persist until a full wipe/re-ingest.

**Gap 1.5: 299 nodes at confidence=0.5 (53% of all nodes).** This is the placeholder confidence value set by `ingest_wiki_page:341` for target nodes created via wikilink MERGE. Even when the target *does* resolve to a real wiki file, the node gets confidence=0.5 instead of 1.0. This means over half the graph is marked as uncertain.

**Gap 1.6: `date` property never populated.** The `Event.date` index was created by `schema.py:36`, but `ingest_wiki_page` never writes `n.date`. The wiki frontmatter has `created` and `updated` fields, but they are parsed and discarded—never stored in Neo4j.

**Gap 1.7: `Entity.type` index is dead.** `schema.py:38` creates `CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)`, but no code path ever sets `n.type`. The index indexes zero values.

**Gap 1.8: `fallback` and `protected` flags always false.** Despite the infrastructure existing in the MERGE query (`n.fallback = $fallback`), no nodes in the graph have `fallback=true` or `protected=true`. The `_is_engineering_only` gate prevents engineering-only pages from reaching Neo4j entirely, but no other path sets these flags.

### 1.5 Label Misassignment

**Gap 1.9: Label inference is name-pattern heavy with narrow tag matching.** `_infer_primary_label` assigns Person based on name patterns (`"Bob Lazar"`, `"David Grusch"`) and only 6 strong tag keywords per label. Tags like `whistleblower` correctly match Person, but tags like `ufo`, `crash`, `technology`, `quantum` don't map to any label. Pages tagged with only content-relevant tags default to `Concept` or `Entity`.

**Gap 1.10: Target nodes get inferred labels from an empty tag context.** When creating target nodes (from wikilinks), `ingest_wiki_page:337` calls `_infer_primary_label(target_display, [])` with an empty tag list. This means target label inference relies purely on name patterns and has no tag signal. A wikilink to `"Area 51"` might correctly infer Place from body context, but a wikilink to `"quantum-computing"` with no tags will default to Entity.

### 1.6 `/events` Endpoint Bug

**Gap 1.11 (CRITICAL): `/events` queries `MATCH (e:Entity)` not `MATCH (e:Event)`.** The endpoint at `main.py:1605` does `MATCH (e:Entity)` — scanning all 560 nodes — then applies client-side keyword filtering to decide if a node "looks like" an event. This is:
- Inefficient (scans entire graph on every request)
- Inaccurate (keyword heuristics miss events and include non-events)
- Not cached (no `@cache_decorator`)
- Fabricates dates from hardcoded heuristics (lines 1650-1661) — `"1933"` → `"1933-06-13T00:00:00Z"`, year tag → `"{year}-06-01T00:00:00Z"` — no actual stored date data is queried

### 1.7 Orphan Nodes

**Gap 1.12: 1 orphan node.** `microsoft q#` exists as an `:Entity` with no relationships and no content_preview. This was likely a wikilink target that was guarded by `_resolve_target_wiki_file` but whose wiki file was later deleted. The reconciliation process (`MATCH (n:Entity) WHERE n.name IN $names DETACH DELETE n`) should handle this but didn't for this specific node.

---

## Part 2: Spacetime Timeline Audit

### 2.1 What the Timeline Actually Is

The timeline in `src/almanac/timeline.py` is a **file-system-based, Neo4j-independent** data structure. It:
- Reads JSON pulse snapshot files from `pulse/{slug}-*.json`
- Runs `git log --follow` on the entity's wiki `.md` file
- Computes `epistemic_confidence`, `social_traction`, `divergence_risk` via `ClaimWavefunction` + divergence engine
- Produces `TimelinePoint[]` objects

**Zero Neo4j queries. Zero graph data. Zero event node lookups.**

### 2.2 Gap: No Connection Between Timeline and Neo4j

**Gap 2.1 (CRITICAL): The timeline has no relationship to the graph database.** The `TimelinePoint` model (`src/models.py:55-62`) has no Neo4j counterpart. The temporal data model documented in `wiki/concepts/temporal-data-model.md` describes three representations ("Time as property", "Time as dimension", "Time as node") — none are implemented.

**Gap 2.2 (CRITICAL): Event nodes have no temporal properties.** Despite `Event` being a node label with 10 nodes, none of them have `date`, `start_date`, `end_date`, `year`, or `timestamp` properties. The `CREATE INDEX FOR (n:Event) ON (n.date)` in `schema.py` indexes an empty property space.

**Gap 2.3: `GET /events` fabricates timestamps.** The endpoint at `main.py:1643-1661` uses hardcoded heuristics:
- Tag scanning for 4-digit numbers (if tag is `"1933"` → use that year)
- String matching for specific event names (`"1944"` in title → `"1944-10-24T00:00:00Z"`)
- Default: `datetime.utcnow().isoformat() + "Z"` for everything else
This means timeline dates are synthetic, not fact-based. An event about "quantum computing" with tag `1994` gets date `"1994-06-01T00:00:00Z"` regardless of when it actually occurred.

**Gap 2.4: No timeline caching.** `build_timeline()` has no `@cache_decorator`. Every request:
- Re-scans the pulse directory for matching files
- Re-runs `git log --follow` (a subprocess)
- Re-computes wavefunction scores for every snapshot
- Re-computes narrative divergence

Latency grows linearly with the number of pulse snapshots and git commits for the entity.

**Gap 2.5: Timeline only covers the last 30 days.** The `days=30` default means historical events more than 30 days old are invisible in the timeline, regardless of pulse data or git history. The `_parse_pulse_snapshots` function filters by `cutoff = datetime.now() - timedelta(days=days)`.

**Gap 2.6: Temporal causality chains don't exist.** The `CAUSED`, `PRECEDED_BY`, `FOLLOWED_BY` relationship types are defined in `SCHEMA_RELATIONSHIPS:56` but are never created (zero occurrences). Event ordering is completely absent from the graph.

### 2.3 What Would Need to Happen for an Accurate Timeline

A production-grade timeline requires:
1. Event nodes with accurate `date` properties (parsed from frontmatter `date` field or inferred from page body)
2. `PRECEDED_BY` and `CAUSED` relationships between dated event nodes
3. A temporal graph query that walks `(n:Event) WHERE n.date IS NOT NULL ORDER BY n.date` with optional branching
4. Cached timeline results with per-entity key (not global invalidation)

---

## Part 3: Search and Application Responsiveness Audit

### 3.1 Architecture: No Server-Side Search

**Gap 3.1 (CRITICAL): The SwiftUI app performs all search client-side.** Three independent search implementations exist, all doing local filtering of bulk-fetched data:

| View | Data Source | Filter Scope |
|---|---|---|
| `WikiBrowserView` | `GET /wiki/pages` (all pages) | By `title` + `tags` only |
| `SidebarDetailsView` | `GET /entities` (all entities into SwiftData) | By `name` only |
| `LoreRepositoryView` | `GET /entities` (all entities into SwiftData) | By `name` only |

**No dedicated `GET /search` or `POST /search` endpoint exists.** The only search-like API is:
- `GET /entities` — returns ALL entities, no filtering possible
- `GET /wiki/pages` — returns ALL pages, optional `?page_type=` filter but no search term

**Gap 3.2: Wiki body content is not searchable.** `WikiBrowserView` filters only on `title` and `tags`. The full markdown body is never fetched until a user taps through to the detail view. If a keyword exists only in the body text, it's invisible to search.

### 3.2 Neo4j Search: CONTAINS Full Scan

**Gap 3.3 (CRITICAL): Server-side search uses `CONTAINS` which is a full label scan.** `search_entities` in `queries.py:66`:
```cypher
MATCH (n:Entity)
WHERE (n.name CONTAINS $term OR n.content_preview CONTAINS $term)
RETURN n LIMIT 15
```
Neo4j BTREE indexes accelerate equality and `STARTS WITH`, not `CONTAINS`. Every search must scan all 560 `:Entity` nodes. With 560 nodes this is ~1ms; with 10k+ it becomes >100ms. No fulltext index exists.

**Gap 3.4: No Neo4j fulltext indexes.** The database schema creates only BTREE indexes (uniqueness constraints + `Event.date` + `Entity.type`). A fulltext index (`CREATE FULLTEXT INDEX ... FOR (n:Entity) ON EACH [n.name, n.content_preview]`) would enable tokenized, ranked fulltext search.

### 3.3 Cache Invalidation Is Too Broad

**Gap 3.5: `invalidate_all()` flushes all cached queries on any write.** Every wiki page save, every ingest call, every entity update calls `cache_store.invalidate_all()`, which clears `cache:neo4j:*`, `cache:llm:*`, `cache:mcp:*`, `cache:test:*`. This means:
- Writing to entity A invalidates cached search results for entity B
- The 300s TTL on cached queries is effectively never reached under write-heavy loads
- No targeted per-entity cache invalidation exists

### 3.4 No Real-Time Updates

**Gap 3.6: No WebSocket or SSE for index changes.** The `/ws/agent` endpoint streams only LLM agent responses. There is no mechanism to push search index updates, new entity notifications, or re-index triggers to connected clients. The SwiftUI app relies entirely on pull-to-refresh.

**Gap 3.7: Status tab polls at 2s but search never auto-updates.** The `StatusDashboardView` has a 2s polling loop for system status, but search results in `WikiBrowserView`, `SidebarDetailsView`, and `LoreRepositoryView` only refresh when the user manually pulls down or navigates away and back.

### 3.5 No Debounce or Search History

**Gap 3.8: No input debounce on any search field.** Every keystroke in `WikiBrowserView`, `SidebarDetailsView`, and `LoreRepositoryView` triggers immediate recomputation of the filter predicate. While currently client-side (fast), this pattern will cause network spam if server-side search is added without debouncing.

**Gap 3.9: No search history.** No `UserDefaults` persistence, no recent searches, no suggestions from past queries.

### 3.6 Rate Limiting Doesn't Differentiate

**Gap 3.10: Read and write endpoints share the same rate limit quota.** The in-memory rate limiter applies the same 20 req/min, burst 5 to all endpoints equally. Search/browsing traffic can exhaust the same quota as heavy ingest operations. There is no differentiated limit for reads vs writes.

### 3.7 Three Separate Search Implementations

**Gap 3.11: No shared search component.** The three search UIs have zero code reuse:

| Aspect | WikiBrowserView | SidebarDetailsView | LoreRepositoryView |
|---|---|---|---|
| Search mechanism | `.searchable()` | Custom text field + overlay | Custom text field |
| Data source | `WikiService.wikiPages` | SwiftData `@Query` | SwiftData `@Query` |
| Filter logic | `title.contains` + `tags.contains` | `name.localizedCaseInsensitiveContains` | `name.localizedCaseInsensitiveContains` |
| Type filter | Button chips | None | Picker + chip |
| Detail navigation | `NavigationLink` → `WikiPageDetailView` | Sheet → `EntityDetailView` | Sheet → `EditAnnotationSheet` |

---

## Part 4: Root Cause Summary

### 4.1 Neo4j Data Quality

| Symptom | Root Cause | Fix |
|---|---|---|
| 53% nodes at confidence=0.5 | Target nodes from wikilinks always get 0.5, even when target page exists | Set confidence=1.0 for resolved targets |
| 81 nodes missing content_preview | Target MERGE doesn't write content_preview | Include content_preview in target MERGE |
| `date` property never set | Frontmatter `created`/`updated` parsed but not written to Neo4j | Add `n.date` from frontmatter |
| `Entity.type` index dead | No code sets `type` property | Remove index or write `type` |
| 3 labels never used | `_infer_primary_label` doesn't consider Algorithm/Paper/QuantumPlatform | Extend inference or add mapping |
| 33% relationships are generic | Heuristic keyword matcher covers ~30 patterns, 20+ relationship types never matched | Expand heuristic mapping |
| `/events` scans all entities | Query is `MATCH (e:Entity)` not `MATCH (e:Event)` | Fix query + add date queries |

### 4.2 Spacetime Timeline

| Symptom | Root Cause | Fix |
|---|---|---|
| Timeline has no date data | Never reads from Neo4j, which has no date properties anyway | 2-part: write dates to Neo4j + make timeline query Neo4j |
| Event timestamps are fabricated | Heuristic tag/year scanning in endpoint code | Store real dates from frontmatter |
| No temporal relationships | `CAUSED`/`PRECEDED_BY` never created | Add temporal inference to ingest pipeline |
| Timeline uncached | `build_timeline()` has no caching | Add `@cache_decorator` with per-entity key |
| Timeline only 30 days | Hardcoded default in `build_timeline()` | Make configurable, support history |
| Timeline independent of Neo4j | Architecture decision never bridged the two | Integrate timeline with Event nodes |

### 4.3 Search/Responsiveness

| Symptom | Root Cause | Fix |
|---|---|---|
| All search is client-side | No `/search` endpoint exists | Add `GET /search?q=` with fulltext index |
| Body content not searchable | Wiki search filters on title+tags only | Extend to include body |
| CONTAINS is full scan | No Neo4j fulltext index | Create `FULLTEXT INDEX` on `name` + `content_preview` |
| Cache invalidated too broadly | `invalidate_all()` on every write | Per-entity cache invalidation |
| No real-time updates | No WebSocket/SSE for index changes | Add SSE endpoint for re-index notifications |
| No debounce | Search fires on every keystroke | Add 300ms debounce when server search is added |
| No search history | Never implemented | Add `UserDefaults`-backed recent searches |
| Rate limiter undifferentiated | Same quota for reads and writes | Separate read/write rate limits |

---

## Part 5: Recommended Priority Order

### Immediate (P0, next session)
1. Fix `/events` endpoint to query `MATCH (e:Event)` instead of `MATCH (e:Entity)` (Gap 1.11)
2. Write `date` property from frontmatter into Neo4j during ingest (Gap 1.6, Gap 2.2)
3. Set confidence=1.0 for resolved target nodes (Gap 1.5)
4. Create Neo4j fulltext index on `name` + `content_preview` (Gap 3.3, Gap 3.4)
5. Add `GET /search?q=` endpoint using fulltext index (Gap 3.1)
6. Add per-entity cache invalidation instead of `invalidate_all()` (Gap 3.5)

### Short-Term (P1, within 2 sessions)
7. Store frontmatter `created`/`updated` dates on Event nodes (Gap 2.2)
8. Expand heuristic keyword mapping to cover more relationship types (Gap 1.3)
9. Remove `Entity.type` index or wire it up (Gap 1.7)
10. Add target node content_preview to target MERGE (Gap 1.4)
11. Add `@cache_decorator` to timeline builder (Gap 2.4)
12. Wire timeline to query Neo4j Event nodes instead of (or in addition to) pulse files (Gap 2.1)

### Medium-Term (P2, 3+ sessions)
13. Unify the three SwiftUI search implementations into a shared component (Gap 3.11)
14. Add SSE endpoint for real-time index change notifications (Gap 3.6)
15. Add debounce to SwiftUI search fields (Gap 3.8)
16. Add search history to SwiftUI (Gap 3.9)
17. Differentiate rate limits for read vs write endpoints (Gap 3.10)
18. Extend label inference to cover Algorithm/Paper/QuantumPlatform (Gap 1.1)
19. Expand timeline beyond 30 days with configurable range (Gap 2.5)

### Long-Term (P3, future milestone)
20. Implement temporal causality chain inference (Gap 2.6)
21. Build graph-wide fulltext search into SwiftUI with ranked results
22. Add wiki body content to search index
23. Implement "Time as node" temporal data model from the concept page
