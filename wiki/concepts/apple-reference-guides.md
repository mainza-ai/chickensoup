---
title: "Apple Reference Guides"
tags: [apple, swift, swiftui, reference, development]
created: 2026-07-11
updated: 2026-07-11
sources: [AppleAdditionalDocumentation]
related: [swift-frontend-architecture, agent-skills, ui-ux-design]
---

# Apple Reference Guides

Coding reference documents for implementing Apple platform features. These guide the LLM when writing Swift/SwiftUI implementation code. Originals imported into `wiki/raw/` from `development-docs/AppleAdditionalDocumentation/`.

## Framework Guides

### AppIntents
`wiki/raw/AppIntents-Updates.md` — AppIntents framework for extending app actions across the system; visual intelligence integration, intent modes, foreground/background execution, property macros, interactive snippets, Spotlight integration

### Liquid Glass Design
`wiki/raw/SwiftUI-Implementing-Liquid-Glass-Design.md` — SwiftUI: `glassEffect()` modifier, shape-morphing transitions, depth-of-field rendering, touch/pointer interactions
`wiki/raw/AppKit-Implementing-Liquid-Glass-Design.md` — AppKit: `NSVisualEffectView` + glass material, layer-backing, `NSAnimationContext`, vibrancy
`wiki/raw/UIKit-Implementing-Liquid-Glass-Design.md` — UIKit: `UIVisualEffectView` + glass vibrancy, `UIViewPropertyAnimator`, `UIPointerInteraction`, UIKit glasstinting
`wiki/raw/WidgetKit-Implementing-Liquid-Glass-Design.md` — WidgetKit: glass background in `WidgetConfiguration`, `AccessoryWidgetFamilies`, `RectangularWidget`, static vs. interactive widget glass

### SwiftUI Integrations
`wiki/raw/SwiftUI-AlarmKit-Integration.md` — AlarmKit framework: `AlarmManager`, one-time/repeating alarms, countdown timers, `AlarmPresentation`, Live Activities, Dynamic Island, Lock Screen, focus/silent override
`wiki/raw/SwiftUI-WebKit-Integration.md` — WebKit in SwiftUI: `WKWebView` with `UIViewRepresentable`, `WKNavigationDelegate`, `WKUserContentController`, JavaScript ↔ Swift bridge, cookie/session management
`wiki/raw/SwiftUI-New-Toolbar-Features.md` — New toolbar features: `ToolbarPlacement`, window toolbars, custom toolbar items, visibility control, toolbar roles
`wiki/raw/SwiftUI-Styled-Text-Editing.md` — Styled text editing: `AttributedString`, `AttributeScopes`, `StyledTextEditor`, inline formatting, custom attributes, NSTextStorage bridging
`wiki/raw/Swift-Charts-3D-Visualization.md` — Swift Charts 3D: `Chart3D`, `PointPlot3D`, `LinePlot3D`, `SurfacePlot3D`, spatial depth marking, 3D mark types, rotation/perspective controls

### Foundation
`wiki/raw/Foundation-AttributedString-Updates.md` — AttributedString framework updates: `AttributeScopes`, `InlinePresentationIntent`, markdown parsing, codable attributes, UIKit/AppKit bridging
`wiki/raw/FoundationModels-Using-on-device-LLM-in-your-app.md` — On-device LLM via FoundationModels: `LLMModel`, `LLMRequest`, `LLMEvaluator`, model loading, permission prompts, local prompt templates

### Swift Language
`wiki/raw/Swift-Concurrency-Updates.md` — Swift concurrency: custom executors, `Actor` improvements, task-local storage, `AsyncStream`/`AsyncSequence` refinements, `distributed actor`, region-based isolation
`wiki/raw/Swift-InlineArray-Span.md` — `InlineArray` (fixed-size stack-allocated array) and `Span` (safe mutable view into contiguous memory); value semantics, zero-cost abstraction over C arrays

### SwiftData
`wiki/raw/SwiftData-Class-Inheritance.md` — SwiftData model class inheritance: abstract models, concrete subclasses, `@Model` inheritance rules, disambiguation, predicate typing, `ModelActor`

### MapKit
`wiki/raw/MapKit-GeoToolbox-PlaceDescriptors.md` — GeoToolbox: `PlaceDescriptor` for semantic location matching, forward/reverse geocoding, landmark detection, `PlaceQuery`, location clustering

### StoreKit
`wiki/raw/StoreKit-Updates.md` — StoreKit 2: `Product`, `PurchaseOption`, `Transaction`, `SubscriptionStoreView`, `StoreView`, win-back offers, `Entitlement`, `Product.SubscriptionInfo`

### Widgets
`wiki/raw/WidgetKit-Implementing-Liquid-Glass-Design.md` — WidgetKit glass (see Liquid Glass above)
`wiki/raw/Widgets-for-visionOS.md` — visionOS widgets: volumetric windows, `WidgetConfiguration` in visionOS, immersive widgets, 3D depth rendering, spatial widget layout

### Vision Intelligence
`wiki/raw/Implementing-Visual-Intelligence-in-iOS.md` — Visual Intelligence: camera object detection, image analysis, scene recognition, `VisualIntelligenceService`, overlay rendering, on-device processing
`wiki/raw/Implementing-Assistive-Access-in-iOS.md` — Assistive Access: simplified UI mode, `AssistiveAccessManager`, feature restrictions, caregiver configuration, accessibility features

## Invocation Convention

When implementing Apple platform features, check this guide list first. Each document covers a specific framework/topic. The raw files in `wiki/raw/` contain full implementation details and code examples.
