---
title: "Swift Concurrency Pro"
tags: [swift, concurrency, agent-skill, twostraws]
created: 2026-06-22
updated: 2026-06-22
sources: [twostraws-swift-concurrency-pro-2026]
related: [swiftui-pro, swiftdata-pro, swift-testing-pro]
---

# Swift Concurrency Pro

An agent skill from Paul Hudson (twostraws) that reviews Swift code for concurrency correctness, modern API usage, and common async/await pitfalls.

## Overview

Source: [twostraws/Swift-Concurrency-Agent-Skill](https://github.com/twostraws/Swift-Concurrency-Agent-Skill)

Installed in `.agents/skills/swift-concurrency-pro/` as part of the four twostraws agent skills.

## What It Covers

- **async/await** — Modern async/await patterns
- **Actors** — Actor isolation, reentrancy
- **Sendable** — Value types, actors, @unchecked Sendable
- **Task groups** — withTaskGroup, withThrowingTaskGroup
- **@concurrent** — Concurrent function execution
- **Structured concurrency** — Preferred over unstructured Task {}
- **Cancellation** — Proper cancellation handling
- **Async streams** — AsyncStream, AsyncSequence
- **Bridging** — Sync/async bridging
- **Interop** — Legacy concurrency migration

## Key Rules

- Target Swift 6.2 or later with strict concurrency checking
- If code spans multiple targets or packages, compare their concurrency build settings
- **Prefer structured concurrency (task groups) over unstructured Task {}**
- **Prefer Swift concurrency over Grand Central Dispatch** for new code
- If an API offers both async/await and closure-based variants, always prefer async/await
- Do not introduce third-party concurrency frameworks without asking first
- **Don't use @unchecked Sendable** to fix compiler errors — it silences the diagnostic without fixing the underlying race
- Prefer actors, value types, or sending parameters instead
- The only legitimate use of @unchecked Sendable is for types with internal locking that are provably thread-safe
- Check actor reentrancy — state may have changed across the await
- Use withTaskGroup instead of creating tasks in a loop

## How It Works

The skill loads its `SKILL.md` and `references/` directory on demand during code review. It checks:
1. Known-dangerous patterns (using `references/hotspots.md`)
2. Swift 6.2 concurrency behavior (using `references/new-features.md`)
3. Actor usage and reentrancy (using `references/actors.md`)
4. Structured vs unstructured concurrency (using `references/structured.md`)
5. Unstructured task correctness (using `references/unstructured.md`)
6. Cancellation handling (using `references/cancellation.md`)
7. Async streams and continuations (using `references/async-streams.md`)
8. Bridging code (using `references/bridging.md`)
9. Legacy concurrency migrations (using `references/interop.md`)
10. Bug patterns (using `references/bug-patterns.md`)
11. Diagnostics (using `references/diagnostics.md`)
12. Async test patterns (using `references/testing.md`)

## Installation

```bash
npx skills add https://github.com/twostraws/Swift-Concurrency-Agent-Skill --skill swift-concurrency-pro
```

## See Also

- [[swiftui-pro]]
- [[swiftdata-pro]]
- [[swift-testing-pro]]
- [[ui-ux-design]]
- [[agent-skills]]
