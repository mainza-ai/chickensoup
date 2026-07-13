---
title: "Frontend Settings Menu — Living Almanac"
tags: [swiftui, frontend, settings, living-almanac, plan]
created: 2026-07-12
updated: 2026-07-12
sources: [living-almanac, frontend-settings-menu, apple-reference-guides]
related: [swift-frontend-architecture, living-almanac, api-design, credibility-scoring, pulse-agent, budget-tracking, ui-ux-design]
---

# Frontend Settings Menu — Living Almanac (Summary)

Full specification lives in `wiki/plan/frontend-settings-menu.md` — the exhaustive 500+ line plan with code snippets for every section.

This page is the index/short version.

## What Needs to Be Built in SwiftUI

### APIModels.swift — 15 new Codable structs

`APIClaimEvidence`, `APIClaimConfidence`, `APIDrivingClaim`, `APIDivergenceResult`, `APIPulseResult`, `APITimelinePoint`, `APITimelineResponse`, `APIPulseHistoryEntry/Response`, `APIBudgetStatus`, `APIAlmanacHistoryEntry/Response`, `APIEntanglementEntry/Response`, `APITribunalResponse/Disagreement`.

### BackendService.swift — 9 new methods

`fetchBudgetStatus()`, `approveBudgetHold()`, `triggerPulse(entityName:handles:)`, `fetchPulseHistory`, `fetchDivergence`, `fetchTimeline`, `fetchEntanglement`, `runTribunal`, `generateAlmanac(dryRun:)`, `fetchAlmanacHistory`.

### SettingsView.swift — New `livingAlmanacSection`

- Network opt-in toggle with local vs network_opt_in tier explanation
- Budget display with progress bar, HOLD banner red, approve button
- Tier-1 entity list with Pulse Now per entity + handles editor (x, subreddit, github)
- Pulse history with platform icons, engagement counts, market odds
- Almanac generation: Dry Run → WKWebView sheet (inline CSS), Live → verify then generate, history list
- Timeline chart: Swift Charts 3D (3 lines epi/trac/div over date) + scrubber (active claims update on drag)
- Entity detail extensions: divergence badge + driving claims, claim confidence rows with epi/trac gauges, no blended number anywhere

### New Views

- `LivingAlmanacTimelineView.swift` — chart + scrubber + detail card
- `ClaimConfidenceRow.swift` — state badge (corroborated green ✓ collapsed / purple ◐ superposition / contested orange / unverified gray) + epi/trac side-by-side

### Design

- Light mode default, #FF9500 accent, 12px radius, 16/24 padding
- SystemOrangeText section headers "LIVING ALMANAC"
- Reuse credentialField pattern for API keys
- onAppear loads budget+pulse+almanac history
- .refreshable on history lists
- Apple guides: `Swift-Charts-3D-Visualization.md`, `SwiftUI-Implementing-Liquid-Glass-Design.md`, `SwiftUI-WebKit-Integration.md`

## Final DOD

See `wiki/plan/frontend-settings-menu.md` Section 4 — manual live test checklist with curl commands:

1. npm install last30days, set .env LAST30DAYS_ENABLED=true BUDGET=20
2. POST /pulse/bob-lazar real CLI → snapshot appears + budget 19.50 + log entry
3. GET divergence + timeline + entanglement → epi != trac visibly
4. POST almanac dry_run true → valid HTML inline CSS no JS dark mode print-friendly, no files/budget
5. POST almanac dry_run false → wiki/raw/almanac/{date}.html+md + log append
6. Mark 2-3 entities tier:1 + let scheduler overnight → dated brief appears unattended

## See Also

- Plan: [[frontend-settings-menu]] (wiki/plan/frontend-settings-menu.md) — full spec with code snippets
- Backend: [[living-almanac]]
- Scoring: [[credibility-scoring]]
- API: [[api-design]]
- Architecture: [[swift-frontend-architecture]]
- Design: [[ui-ux-design]], [[apple-reference-guides]]
