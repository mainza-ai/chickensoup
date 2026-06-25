---
created: 2026-06-22
protected: true
related:
- ui-ux-design
- swiftui-pro
- swiftdata-pro
- swift-concurrency-pro
- swift-testing-pro
sources:
- twostraws-2026
tags:
- agent
- skills
- swift
- twostraws
title: Agent Skills
updated: '2026-06-25'
---

# Agent Skills

Four agent skills from Paul Hudson (twostraws) are installed in `.agents/skills/` and automatically referenced during Swift implementation.

## Overview

All four skills target **iOS 26+ and Swift 6.4**, are written by Paul Hudson (who writes actively updated books and tutorials), and are licensed under MIT. They're designed to be installed via `npx skills add` into Claude Code, Codex, Gemini, Cursor, and OpenCode.

Each skill has a `SKILL.md` and a `references/` directory with detailed rules loaded on demand during code review. This means the AI only loads what it needs, keeping token usage efficient.

## Skills

### SwiftUI Pro

Source: [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill)

Covers: iOS 26+ APIs, deprecated API, VoiceOver, performance, navigation, data flow, animations, design, accessibility.

Common LLM mistakes this targets:
- Invisible VoiceOver buttons
- Deprecated API usage
- Poor data flow
- Performance surprises
- Incorrect animations

### SwiftData Pro

Source: [twostraws/SwiftData-Agent-Skill](https://github.com/twostraws/SwiftData-Agent-Skill)

Covers: @Model, @Query, predicates, indexes, migrations, relationships, iCloud sync, class inheritance.

Key rules:
- @Query must only be used inside SwiftUI views
- isEmpty == false crashes at runtime — use !isEmpty
- iOS 26+ class inheritance patterns
- CloudKit-specific constraints

### Swift Concurrency Pro

Source: [twostraws/Swift-Concurrency-Agent-Skill](https://github.com/twostraws/Swift-Concurrency-Agent-Skill)

Covers: async/await, actors, Sendable, task groups, @concurrent, structured concurrency, cancellation, async streams, bridging, interop.

Key rules:
- Don't use @unchecked Sendable to silence errors
- Prefer actors, value types, or sending parameters
- Prefer structured concurrency (task groups) over unstructured Task {}
- Prefer async/await over closure-based variants
- Swift 6.4 strict concurrency checking

### Swift Testing Pro

Source: [twostraws/Swift-Testing-Agent-Skill](https://github.com/twostraws/Swift-Testing-Agent-Skill)

Covers: @Test, #expect, #require, parameterized tests, traits, exit tests, confirmations.

Key rules:
- Swift Testing does NOT support UI tests — use XCTest for UI tests
- Use struct, not class, for test suites
- Use #expect for expectations, #require for preconditions
- init/deinit over setUp/tearDown
- Parallel execution

## Installation

Installed via `npx skills add` into `.agents/skills/`:

```bash
npx skills add https://github.com/twostraws/swiftui-agent-skill --skill swiftui-pro
npx skills add https://github.com/twostraws/SwiftData-Agent-Skill --skill swiftdata-pro
npx skills add https://github.com/twostraws/Swift-Concurrency-Agent-Skill --skill swift-concurrency-pro
npx skills add https://github.com/twostraws/Swift-Testing-Agent-Skill --skill swift-testing-pro
```

## Usage

The skills are automatically referenced when implementing Swift code. They can also be triggered manually:

- **SwiftUI Pro:** `#swiftui-pro` or "Use SwiftUI Pro to review this code"
- **SwiftData Pro:** `#swiftdata-pro` or "Use SwiftData Pro to check my models"
- **Swift Concurrency Pro:** `#swift-concurrency-pro` or "Use Swift Concurrency Pro to review concurrency"
- **Swift Testing Pro:** `#swift-testing-pro` or "Use Swift Testing Pro to review tests"

## See Also

- [[ui-ux-design]]
- [[swiftui-pro]]
- [[swiftdata-pro]]
- [[swift-concurrency-pro]]
- [[swift-testing-pro]]

