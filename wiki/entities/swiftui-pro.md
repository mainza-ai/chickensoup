---
created: 2026-06-22
protected: true
related:
- swiftui
- swiftdata-pro
- swift-concurrency-pro
- swift-testing-pro
sources:
- twostraws-swiftui-pro-2026
tags:
- swift
- swiftui
- agent-skill
- twostraws
title: SwiftUI Pro
updated: '2026-06-25'
---

# SwiftUI Pro

An agent skill from Paul Hudson (twostraws) that provides comprehensive review of SwiftUI code for best practices on modern APIs, maintainability, and performance.

## Overview

Source: [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill)

Installed in `.agents/skills/swiftui-pro/` as part of the four twostraws agent skills.

## What It Covers

- **iOS 26+ APIs** — Uses the latest Swift and SwiftUI APIs
- **Deprecated API** — Flags deprecated API usage
- **VoiceOver** — Accessibility compliance
- **Performance** — Efficient rendering and animations
- **Navigation** — NavigationStack, NavigationSplitView, navigationDestination
- **Data Flow** — Proper data flow patterns
- **Animations** — Animatable macro, animation with value, chaining
- **Design** — Apple HIG compliance, semantic colors, SF Pro typography
- **Accessibility** — Dynamic Type, VoiceOver, Reduce Motion

## Key Rules

- iOS 26 exists, and is the default deployment target for new apps
- Target Swift 6.2 or later, using modern Swift concurrency
- Avoid UIKit unless requested
- Don't introduce third-party frameworks without asking first
- Break different types into different Swift files
- Use a consistent project structure, with folder layout determined by app features
- Use `foregroundStyle()` instead of `foregroundColor()`
- Use `clipShape(.rect(cornerRadius:))` instead of `cornerRadius()`
- Use `Tab` API instead of `tabItem()`
- Use `#Preview` instead of `PreviewProvider`
- Icon-only buttons should have a text label for VoiceOver
- Avoid `Binding(get:set:)` in view body — use `@State` with `onChange()` instead
- Use `ContentUnavailableView` when data is missing or empty
- Use `Label` over `HStack` for icon + text
- Use `bold()` instead of `fontWeight(.bold)`
- Minimum tap area is 44x44
- Use `LabeledContent` for title-value display

## How It Works

The skill loads its `SKILL.md` and `references/` directory on demand during code review. It checks:
1. Deprecated API (using `references/api.md`)
2. Views, modifiers, animations (using `references/views.md`)
3. Data flow (using `references/data.md`)
4. Navigation (using `references/navigation.md`)
5. Design and HIG (using `references/design.md`)
6. Accessibility (using `references/accessibility.md`)
7. Performance (using `references/performance.md`)
8. Swift code (using `references/swift.md`)
9. Code hygiene (using `references/hygiene.md`)

## Installation

```bash
npx skills add https://github.com/twostraws/swiftui-agent-skill --skill swiftui-pro
```

## See Also

- [[swiftdata-pro]]
- [[swift-concurrency-pro]]
- [[swift-testing-pro]]
- [[ui-ux-design]]
- [[agent-skills]]

