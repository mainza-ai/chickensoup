---
title: "Frontend Settings Menu — Living Almanac To Final DOD"
tags: [project, frontend, swiftui, living-almanac, settings, DOD]
created: 2026-07-12
updated: 2026-07-12
sources: [living-almanac, api-design, credibility-scoring, swift-frontend-architecture, apple-reference-guides]
related: [living-almanac, api-design, credibility-scoring, swift-frontend-architecture, agent-architecture, ui-ux-design, key-decisions]
---

# Frontend Settings Menu — Living Almanac to Final DOD

Production SwiftUI plan to expose the Living Almanac in Settings and to reach final DOD: a dated autonomous brief appears unattended.

## 0. Current SettingsView Inventory

`SettingsView.swift` already has:

- Brand header + header banner
- `backendPickerSection` — NumPy/Qiskit/D-Wave/IBM/IonQ picker with description per backend
- `llmConfigSection` — provider (auto/omlx/ollama/lmstudio) picker with probe, model picker, apply button
- `chatToWikiSection` — auto-convert toggle, notify toggle, min conversation length stepper, user name rename, wiki backup export
- `apiTokenSection` — hardware toggle + IBM/D-Wave/IonQ tokens with show/hide + active-on-server indicator
- `saveButtonSection` — save quantum config

Services in `Shared/Services/`:
- `BackendService` (@MainActor Observable, shared singleton) — central; holds `graph = GraphService.shared`, `wiki = WikiService.shared`, `chat = ChatService.shared`, `config = ConfigService.shared`; manages timeline events/entities, query with conversation_id, geodesic solve, graph neighborhoods
- `ConfigService` — fetches/saves quantum backend + LLM provider/model, probe provider
- `ChatService` — chat ingest status, manual trigger, user name, history/notifications
- `WikiService` — pages listing/detail/delete/export/import
- `GraphService` — neighborhood fetch, navigation history stack
- `LLMDiscoveryService` — probes oMLX/Ollama/LM Studio, chain status indicators

Networking:
- `APIClient` actor singleton, `request<T: Decodable>` with ISO8601 decoding, 90s timeout, 5 error types, base `http://127.0.0.1:8000`
- `APIModels` 822 lines, 20+ Codable structs

## 1. What Must Be Added — 8 New Sections

### 1.1 APIModels Additions

New Codable structs mirroring new Pydantic models:

```swift
public struct APIClaimEvidence: Codable {
    var claim_text: String
    var source_platform: String
    var engagement_count: Int
    var url: String
    var timestamp: String
    var cluster_id: String
    var polymarket_odds: Double?
    var engagement_decayed: Double?
    var provenance_chain: [String]
}

public struct APIClaimConfidence: Codable {
    var epistemic_confidence: Double
    var social_traction: Double
    var state_label: String // corroborated | contested | unverified
    var collapsed: Bool
    var evidence_count: Int
    var last_pulse_at: String?
    var scoring_version: String
    var scoring_inputs: [String: AnyCodable]? // AnyCodable wrapper
    var claim_text: String?
}

public struct APIDrivingClaim: Codable {
    var claim_text: String
    var platform: String
    var old_confidence: Double?
    var new_confidence: Double
    var delta: Double
}

public struct APIDivergenceResult: Codable {
    var entity_name: String
    var divergence_risk: Double
    var canon_vector_hash: String
    var live_vector_hash: String
    var driving_claims: [APIDrivingClaim]
    var computed_at: String
}

public struct APIPulseResult: Codable {
    var entity_name: String
    var status: String // success, disabled, budget_exceeded, error, no_data
    var evidence: [APIClaimEvidence]
    var raw_snapshot_path: String?
    var budget_remaining: Double
    var error: String?
}

public struct APITimelinePoint: Codable {
    var date: String
    var epistemic_confidence: Double
    var social_traction: Double
    var divergence_risk: Double
    var active_claims: [String]
    var pulse_file: String?
    var wiki_commit: String?
}

public struct APITimelineResponse: Codable {
    var entity_name: String
    var days: Int
    var points: [APITimelinePoint]
    var total: Int
}

public struct APIPulseHistoryEntry: Codable {
    var entity_name: String
    var date: String
    var timestamp: String
    var evidence_count: Int
    var file: String
}

public struct APIPulseHistoryResponse: Codable {
    var pulses: [APIPulseHistoryEntry]
    var total: Int
}

public struct APIBudgetStatus: Codable {
    var month_key: String
    var spent_usd: Double
    var pulls_count: Int
    var remaining_usd: Double
    var ceiling_usd: Double
    var on_hold: Bool
}

public struct APIAlmanacHistoryEntry: Codable {
    var date: String
    var filename: String
    var path: String
    var size_kb: Double
    var created: String
}

public struct APIAlmanacHistoryResponse: Codable {
    var almanacs: [APIAlmanacHistoryEntry]
    var total: Int
}

public struct APIEntanglementEntry: Codable {
    var entity_a: String
    var entity_b: String
    var entanglement_score: Double
    var co_occurrence_count: Int
    var independent_platforms: [String]
    var independent_clusters: Int
    var is_strong: Bool
    var meyer_wallach_raw: Double?
}

public struct APIEntanglementResponse: Codable {
    var entity_name: String
    var entanglements: [APIEntanglementEntry]
    var total: Int
}

public struct APITribunalResponse: Codable {
    var triggered: Bool
    var claim_text: String?
    var wavefunction: [String: AnyCodable]?
    var divergence_risk: Double?
    var skeptic_position: String?
    var empiricist_position: String?
    var believer_position: String?
    var skeptic_citations: [String]?
    var empiricist_citations: [String]?
    var believer_citations: [String]?
    var referee_synthesis: String?
    var final_state_label: String?
    var disagreements: [APITribunalDisagreement]?
    var all_citations: [String]?
}

public struct APITribunalDisagreement: Codable {
    var topic: String?
    var skeptic: String?
    var empiricist: String?
    var believer: String?
    var resolution: String?
}
```

### 1.2 BackendService Extensions

Add to `BackendService.swift`:

```swift
// MARK: - Living Almanac / Pulse / Budget

@MainActor
public func fetchBudgetStatus() async -> APIBudgetStatus? { /* GET /budget/status */ }

@MainActor
public func approveBudgetHold() async -> Bool { /* POST /budget/approve */ }

@MainActor
public func triggerPulse(entityName: String, handles: [String: String]? = nil) async -> APIPulseResult?

@MainActor
public func fetchPulseHistory(entityName: String? = nil, limit: Int = 50) async -> APIPulseHistoryResponse?

@MainActor
public func fetchDivergence(entityName: String) async -> APIDivergenceResult?

@MainActor
public func fetchTimeline(entityName: String, days: Int = 30) async -> APITimelineResponse?

@MainActor
public func fetchEntanglement(entityName: String, candidate: String? = nil) async -> APIEntanglementResponse?

@MainActor
public func runTribunal(entityName: String, claimText: String, divergenceRisk: Double = 0.0) async -> APITribunalResponse?

@MainActor
public func generateAlmanac(dryRun: Bool = true) async -> APIAlmanacGenerateResponse?

@MainActor
public func fetchAlmanacHistory(limit: Int = 20) async -> APIAlmanacHistoryResponse?
```

- Each method uses `APIClient.shared.request<T>(path, method, body, query)` pattern matching existing `fetchConfig()` etc.
- Store `budgetStatus: APIBudgetStatus?`, `lastPulseResults: [APIPulseResult]`, `almanacHistory: [APIAlmanacHistoryEntry]` as `@Published` or `@Observable` state for UI binding.
- Error handling reuses existing `lastError: APIError?` pattern.

### 1.3 New Living Almanac Settings Section

New `@ViewBuilder private var livingAlmanacSection: some View` in `SettingsView.swift`:

#### Subsection: Network Opt-In Toggle

```
Toggle LAST30DAYS_ENABLED — "Enable Live Evidence (last30days)"
Label: "When enabled, the backend shells out to last30days CLI for Reddit/X/YouTube/news evidence. Clearly labeled as network-dependent tier."
- Binding to GET /config + POST /config with new field last30days_enabled (needs ConfigService extension + env var LAST30DAYS_ENABLED)
- When disabled: show "Local-first only — no network evidence" indicator, disable downstream controls, Budget section shows disabled state, Pulse buttons disabled, Almanac generate disabled except dry-run showing "Enable live evidence first"
- Source tier labeling: explain local vs network_opt_in per spec non-negotiable #2
```

#### Subsection: Budget Display

```
- GET /budget/status on appear + pull-to-refresh
- Show: Month key, spent $X.XX of $Y.00 ceiling, pulls count, remaining $Z.ZZ, HOLD flag
- Progress bar: spent / ceiling, orange fill, red when >80%
- If on_hold: red banner "Budget on HOLD — remaining $ < 2× cost per pull. Requires approval."
- Button "Approve HOLD" → POST /budget/approve → refresh status
- Explanatory text: "Hard monthly ceiling. Each pulse costs ~$0.50. Lua atomic check before every pull — refusal logged not silently throttled."
- Persist last checked timestamp
```

#### Subsection: Entities & Tiers

```
- List Tier-1 entities: GET /wiki/pages? type=entities, filter where frontmatter tier==1 or last30days_handles present (need wiki API extension or compute locally)
- Display: slug, title, handles (x, subreddit, github), tier badge
- Button per entity: "Pulse Now" → POST /pulse/{entity_name} with optional handles
- Show pulse result: status (success/disabled/budget_exceeded/error/no_data), evidence count, remaining budget, raw_snapshot_path link to wiki/raw/pulse/ (in Wiki browser)
- Handle input: optional dict editor for x, subreddit, github (small form per entity)
```

#### Subsection: Pulse History

```
- List recent pulses from GET /pulse/history?limit=50
- Each entry: entity, date, evidence_count, file path, timestamp
- Tap to show detail: evidence list with platform icons, engagement counts, market odds, cluster ids, URLs
- Filter by entity name search bar
```

#### Subsection: Almanac Generation

```
- Two buttons: "Dry Run" and "Generate Live"
- Dry Run: POST /almanac/generate?dry_run=true → returns html_content inline, show in sheet with inline CSS rendered (WKWebView)
  - Label: "Dry run produces brief without file writes or budget spend — verification before first live run"
- Live: POST /almanac/generate?dry_run=false → writes wiki/raw/almanac/{date}.html+, log.md append
  - Requires LAST30DAYS_ENABLED=true and budget not on HOLD — guard with alert if not
- Almanac History: GET /almanac/history → list of dated briefs, tap to open in WKWebView (self-contained HTML, no JS, dark mode via media query)
- Show elapsed_seconds, entities_processed, moved/collapsed/contested counts
- Idempotency note: "If hash unchanged since last run, logs 'no material change' instead of redundant brief"
```

### 1.4 New Timeline Slider View (Separate Feature, not Settings)

`Features/Timeline/Views/LivingAlmanacTimelineView.swift` — uses `fetchTimeline(entityName:days:)` :

- Time range picker: 7, 14, 30, 60, 90 days segmented control
- Chart: Swift Charts 3D or 2D line chart from `wiki/raw/Swift-Charts-3D-Visualization.md` — 3 lines: epistemic_confidence, social_traction, divergence_risk over date
- Scrubbing slider: user drags across time, active claims list updates
- Detail card per point: active_claims[], wiki_commit SHA with link to detail, pulse_file link
- Fetch: debounced on entity selection + days change
- Offline: show cached points with "last synced" indicator

Mapping to Apple guide: `Swift-Charts-3D-Visualization.md` for chart implementation, `SwiftUI-Implementing-Liquid-Glass-Design.md` for card styling.

### 1.5 New Entity Detail Extensions

In `EntityDetailView.swift` / `WikiPageDetailView.swift`:

- If `divergence` present on `WikiPageDetailResponse`: show divergence risk badge + driving claims list
- If `claim_confidences` present: show per-claim waveform row:
  - State badge: corroborated (green ✓ collapsed / purple ◐ superposition) vs contested (orange) vs unverified (gray)
  - epi/trac gauges side-by-side (separate, never merged)
  - Collapsed indicator, evidence_count, last_pulse_at
  - Expand to show `scoring_inputs`: diversity, engagement_mag, market_prior, contradiction, platforms, backend (AerEstimatorV2 etc.)
- Button "View Timeline" → navigate to `LivingAlmanacTimelineView` for this entity
- Button "Entanglement Map" → show correlated entities with Meyer-Wallach scores

### 1.6 ConfigService Extension

Add `last30daysEnabled: Bool`, `monthlyBudget: Double`, `costPerPull: Double` to config request/response:

```swift
public struct APIConfigResponse { 
    // existing...
    var last30daysEnabled: Bool
    var budgetRemaining: Double?
}

func saveLast30daysConfig(enabled: Bool, monthlyBudget: Double?) async -> Bool {
    // POST /config with additional fields OR dedicated POST /config/last30days
}
```

Backend already exposes `last30days_enabled` in `/status` and will need `/config` extended to accept `LAST30DAYS_ENABLED` (currently not in `ConfigRequest` — needs backend config endpoint update OR `.env` editing via settings UI note "Edit .env and restart backend" if dynamic config not yet supported).

Simplest for final DOD: Settings UI says "Set LAST30DAYS_ENABLED=true in .env and restart uvicorn" with copy-paste command, plus budget ceiling is read-only display with HOLD approve button. Pulse trigger and almanac generate work without additional config changes.

## 2. Design Alignment

Per `wiki/concepts/ui-ux-design.md`:
- Light mode default, #FF9500 accent, rounded corners 12px, card background, glass border, 16pt standard padding, 24pt loose
- SystemOrangeText for section headers "LIVING ALMANAC" caption bold
- Use existing `credentialField()` pattern for API keys (already shows lock.shield for active-on-server)
- Reuse `ProgressView` 0.7 scale for probe states, Capsule background for save message success/failure
- `onAppear` loads budget + pulse history + almanac history
- Pull-to-refresh on history lists via `.refreshable`

Per `wiki/raw/SwiftUI-Implementing-Liquid-Glass-Design.md` for timeline chart cards.

## 3. Implementation Order (Same Sequence as Backend PRs)

1. APIModels + BackendService methods for budget/status/pulse (foundation)
2. Living Almanac Settings subsection: budget display + HOLD approve + toggle note
3. Pulse Now per entity + pulse history list
4. Timeline chart view (uses cached pulse JSON + new endpoint)
5. Entity detail divergence + claim confidence rows
6. Almanac generation section (dry-run sheet + history list with WKWebView)
7. (Stretch) Entanglement map visualization

## 4. Final DOD Checklist — To Reach Self-Publishing Brief

### Manual Live Test (Dev Machine)

1. `npm install -g last30days` or ensure `npx last30days --help` works
2. In `.env`:
   ```
   LAST30DAYS_ENABLED=true
   LAST30DAYS_MONTHLY_BUDGET_USD=20.0
   LAST30DAYS_COST_PER_PULL_USD=0.50
   ```
3. Restart backend: `uv run uvicorn src.main:app --reload`
4. Verify `GET /status` returns `last30days_enabled=true, budget_remaining=20.0`
5. Trigger one real pulse:
   ```
   curl -X POST http://127.0.0.1:8000/pulse/bob-lazar \
     -H "X-API-Key: $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"handles":{"x":"@bob_lazar","subreddit":"ufos"}}'
   ```
   Expected: `status=success`, evidence array, `raw_snapshot_path=wiki/raw/pulse/bob-lazar-2026-07-12.json`, budget now 19.50, `log.md` entry `pulse | Bob Lazar | N evidence | $0.50 | remaining=$19.50`
6. Check scoring:
   ```
   curl http://127.0.0.1:8000/entities/bob-lazar/divergence
   curl "http://127.0.0.1:8000/entities/bob-lazar/timeline?days=30"
   curl http://127.0.0.1:8000/entities/bob-lazar/entanglement
   ```
   Social traction and epistemic confidence visibly different numbers.
7. Dry-run almanac:
   ```
   curl -X POST "http://127.0.0.1:8000/almanac/generate?dry_run=true" \
     -H "X-API-Key: $API_KEY"
   ```
   → Valid HTML (inline CSS, no JS, dark mode media query, print-friendly), no file writes, no budget decrement.
8. Live almanac after manual approval of HTML:
   ```
   curl -X POST "http://127.0.0.1:8000/almanac/generate?dry_run=false" \
     -H "X-API-Key: $API_KEY"
   ```
   → `wiki/raw/almanac/2026-07-12.html` + `.md`, `log.md` append `almanac | 2026-07-12 | ...`, HTML self-contained works when opened in browser
9. Mark 2-3 entities `tier: 1` in frontmatter + confirm `src/almanac/almanac_generator.py:_load_tier_entities()` discovers them
10. Let scheduler run overnight (`ALMANAC_GENERATION_INTERVAL_HOURS=24`): by morning, new dated brief in `wiki/raw/almanac/` appears with real sourced content, nobody touched it — **this last part is the whole point**

### SwiftUI Settings DOD

- [ ] Budget section shows live spend/remaining/HOLD with approve button
- [ ] Pulse Now per Tier-1 entity works and shows evidence count
- [ ] Pulse history list with platform icons and engagement
- [ ] Almanac dry-run sheet renders self-contained HTML with inline CSS (use `WKWebView` or `WebKit` `ObservedObject`)
- [ ] Almanac history list with date, size, tap to open full brief
- [ ] Timeline scrubber chartable (epi + traction + divergence over time) per entity
- [ ] Entity detail shows divergence risk + claim confidence rows with distinct epi/trac
- [ ] No blended confidence number anywhere in UI — social traction and epistemic always two columns/badges

### Production Guards

- [ ] All 11 existing tests still pass (no regression)
- [ ] New 8 test files (pulse, budget, wavefunction, divergence, entanglement, tribunal, timeline, almanac) pass
- [ ] `POST /pulse/{entity}; rm -rf /` does not execute shell (test_pulse_never_shell_true)
- [ ] Budget refusal logs, does not silently throttle
- [ ] Disabled returns no-op not error
- [ ] Uncontested never triggers tribunal (0 LLM calls)
- [ ] `LOG_IGNORE_PATTERNS` prevents pytest pollution of log.md
- [ ] HTML brief valid (no unclosed tags), self-contained (no external CSS/JS), dark mode, print-friendly

## 5. Cross-References

- Spec: `development-docs/chickensoup-living-almanac-implementation-spec.md` (ground truth)
- Backend plan: [[living-almanac]]
- Quantum docs: [[field-geometry-tensor]], [[credibility-scoring]], [[quantum-state-representation]]
- Apple guides: [[apple-reference-guides]] → `Swift-Charts-3D-Visualization.md`, `SwiftUI-Implementing-Liquid-Glass-Design.md`, `SwiftUI-WebKit-Integration.md`, `WidgetKit-Implementing-Liquid-Glass-Design.md`
- Agent skills: [[swiftui-pro]], [[swiftdata-pro]], [[swift-concurrency-pro]], [[swift-testing-pro]]
- Pipeline: [[chat-to-wiki-pipeline]], [[ingestion-pipeline]], [[wiki-file-system]]
- API: [[api-design]]
- Frontend arch: [[swift-frontend-architecture]]

## 6. Definition of Done — This Project

Run `pulse_agent` against a real entity with `LAST30DAYS_ENABLED=true` and a small budget. Confirm: a raw evidence file appears, a wavefunction score computes with a visible, auditable trail of what produced it, a divergence score computes against the existing wiki page, social traction and epistemic confidence are visibly different numbers, and — if you let the scheduler run overnight — a dated almanac HTML file appears in the morning with real sourced content and nobody touched it. That last part is the whole point.

## See Also

- [[living-almanac]] — backend implementation
- [[credibility-scoring]] — wavefunction details
- [[api-design]] — new endpoints
- [[ui-ux-design]] — design system
- [[apple-reference-guides]] — coding refs for charts + liquid glass + WebKit
