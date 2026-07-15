# AGENTS.md

## Time Travel Wiki Schema

This is the wiki for our UFO/Aliens/Time Travel project. The wiki is maintained by the LLM — you (the human) curate and ask questions; the LLM writes, updates, and cross-references.

### Directory Structure

```
wiki/
  overview.md          # Top-level summary of everything
  index.md             # Content-oriented catalog (updated on every ingest)
  log.md               # Append-only chronological log
  entities/            # Specific things, people, places, programs
  concepts/            # Ideas, theories, frameworks
  projects/            # Time travel machinery project-specific
  raw/                 # Immutable source documents
  dev/                 # Engineering documentation — NOT ingested to Neo4j (engineering-only tags)
  plan/                # Implementation plans and audits — NOT ingested to Neo4j
```

### Dev Pages Rule

Pages in `wiki/dev/` and `wiki/plan/` have `ENGINEERING_TAGS` (architecture, design, api, config, etc.) and NO `CONTENT_TAGS` — they are **engineering-only**, protected from Neo4j ingest. They are documentation for the LLM, not user-facing content.

**When you modify code, update the relevant dev wiki page to match.** The key dev pages are:

| Wiki Page | Code it documents | Keep updated when |
|-----------|------------------|-------------------|
| `dev/project-structure.md` | Full source tree layout | Adding/removing files, changing sizes |
| `dev/api-design.md` | All endpoints in `main.py` | Adding/removing routes |
| `dev/agent-architecture.md` | Agent files in `src/agents/` | Adding agents, changing architecture |
| `dev/pydantic-settings.md` | Settings in `src/config.py` | Adding/removing env vars |

Check `src/wiki/cleanup.py` for the authoritative `ENGINEERING_TAGS` set.

### Page Format

All wiki pages use YAML frontmatter:

```yaml
---
title: "Page Title"
tags: [ufo, time-travel, ai]
created: 2026-06-22
updated: 2026-06-22
sources: [Grusch-2023, Lazar-1989, Nimitz-2004]
related: [uap, field-manipulation, ai-alien-connection]
---
```

### Page Types

- **Entity pages** (`entities/`): Specific things — people, craft, places, programs. Focus on what it is, what we know, what's uncertain.
- **Concept pages** (`concepts/`): Ideas, theories, frameworks. Focus on the argument, evidence for/against, and connections to other concepts.
- **Project pages** (`projects/`): Time travel machinery. Architecture, components, decisions, tradeoffs.

### Operations

1. **Ingest**: Read source → discuss takeaways → write/update pages → update index and log
2. **Query**: Search index → read relevant pages → synthesize answer → file useful answers as new pages
3. **Lint**: Check for contradictions, stale claims, orphans, missing cross-references

### Cross-references

- Use `[[wikiname]]` syntax for internal links (Obsidian convention)
- Cross-references should be explicit and bidirectional where possible
- When a page references another, the referenced page should also link back

## Apple Platform Reference Guides

Full coding references live in `wiki/raw/` (imported from `development-docs/AppleAdditionalDocumentation/`). The master index is at [[apple-reference-guides]].

### Available Guides
- **AppIntents**: `wiki/raw/AppIntents-Updates.md` — system action extensions, visual intelligence integration, intent modes, interactive snippets
- **Liquid Glass Design**: `wiki/raw/SwiftUI-Implementing-Liquid-Glass-Design.md`, `wiki/raw/AppKit-Implementing-Liquid-Glass-Design.md`, `wiki/raw/UIKit-Implementing-Liquid-Glass-Design.md`, `wiki/raw/WidgetKit-Implementing-Liquid-Glass-Design.md` — glass material, shape-morphing, depth-of-field, touch/pointer
- **AlarmKit**: `wiki/raw/SwiftUI-AlarmKit-Integration.md` — alarms, timers, Live Activities, Dynamic Island, focus override (784 lines)
- **WebKit**: `wiki/raw/SwiftUI-WebKit-Integration.md` — WKWebView embedding, JS bridge, cookie management
- **FoundationModels (on-device LLM)**: `wiki/raw/FoundationModels-Using-on-device-LLM-in-your-app.md` — local LLM inference via FoundationModels
- **Foundation AttributedString**: `wiki/raw/Foundation-AttributedString-Updates.md` — AttributeScopes, markdown parsing, codable attributes
- **Swift Charts 3D**: `wiki/raw/Swift-Charts-3D-Visualization.md` — Chart3D, point/line/surface plots, spatial depth
- **Swift Concurrency**: `wiki/raw/Swift-Concurrency-Updates.md` — custom executors, distributed actor, region-based isolation
- **Swift InlineArray/Span**: `wiki/raw/Swift-InlineArray-Span.md` — fixed-size stack arrays, safe mutable contiguous memory views
- **SwiftData**: `wiki/raw/SwiftData-Class-Inheritance.md` — @Model inheritance, abstract models, ModelActor typing
- **MapKit GeoToolbox**: `wiki/raw/MapKit-GeoToolbox-PlaceDescriptors.md` — PlaceDescriptor, semantic location, geocoding
- **StoreKit 2**: `wiki/raw/StoreKit-Updates.md` — Products, Purchases, StoreView, win-back offers, subscriptions
- **visionOS Widgets**: `wiki/raw/Widgets-for-visionOS.md` — volumetric widgets, 3D depth, spatial layout
- **Visual Intelligence**: `wiki/raw/Implementing-Visual-Intelligence-in-iOS.md` — camera detection, scene recognition, on-device
- **Assistive Access**: `wiki/raw/Implementing-Assistive-Access-in-iOS.md` — simplified UI mode, caregiver config

### Invocation Convention
When the LLM needs to write Apple platform code, it should:
1. Check [[apple-reference-guides]] for the relevant guide
2. Read the raw file from `wiki/raw/` for implementation details and code examples
3. Also consult relevant agent skills ([[swiftui-pro]], [[swiftdata-pro]], [[swift-concurrency-pro]], [[swift-testing-pro]])

## SwiftUI Pro Skill Rules

When writing or reviewing SwiftUI code, ALWAYS load the `swiftui-pro` skill and follow these rules strictly. This is a production app — no shortcuts, no simplifications that would require rework.

### File Organization
- Each type (struct, class, enum, actor) gets its own Swift file. Do not place multiple types in a single file.
- Computed `some View` properties must be extracted into separate `View` structs, each in its own file. Exceptions only for tiny, trivial helpers that would be 3-5 lines inlined.
- Use `#Preview` for previews, never `PreviewProvider`.

### Views
- Button actions must be extracted into separate methods, not inline closures in `body`.
- Prefer `Button("Label", systemImage: "plus", action: myAction)` syntax over `Button { action() }`.
- Never use `onTapGesture()` — use `Button` or `.accessibilityAction()` instead.
- `body` properties must be kept short. Extract sub-views aggressively.

### Data Flow
- `@Observable` classes must be marked `@MainActor`.
- `@State` must be `private` and owned by the creating view only.
- Never use `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, or `@EnvironmentObject` unless unavoidable.
- Avoid `Binding(get:set:)` in `body` — use `@State` with `onChange()` instead.
- Structs should conform to `Identifiable` rather than using `id: \.property`.

### Performance
- Avoid `AnyView`. Use `@ViewBuilder`, `Group`, or generics.
- Use `LazyVStack`/`LazyHStack` for large scrolling data sets.
- Prefer `task()` over `onAppear()` for async work (auto-cancels on disappear).
- Never use `animation(_:)` without a `value` parameter.
- Use ternary expressions for toggling modifiers instead of `if`/`else` branches.

### Accessibility
- Buttons with images must always include text labels for VoiceOver, even if visually icon-only (use `.labelStyle(.iconOnly)` to hide the text visually).
- Use `.accessibilityLabel()` on ambiguous icons.
- Respect Dynamic Type — use `.font(.body)`, `.headline`, etc. Avoid fixed font sizes.
- If color is a differentiator, add icons/patterns for `accessibilityDifferentiateWithoutColor`.

### Modifiers Order & Style (from hygiene.md)
- `.font()` then `.foregroundStyle()` then `.padding()` then `.background()` then `.clipShape()` then `.overlay()`
- All modifiers on separate lines, indented to match

## Lint Checklist

- [ ] Contradictions between pages
- [ ] Stale claims superseded by newer sources
- [ ] Orphan pages with no inbound links
- [ ] Important concepts without their own page
- [ ] Missing cross-references
- [ ] Data gaps
