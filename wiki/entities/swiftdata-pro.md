---
title: "SwiftData Pro"
tags: [swift, swiftdata, agent-skill, twostraws]
created: 2026-06-22
updated: 2026-06-22
sources: [twostraws-swiftdata-pro-2026]
related: [swiftui-pro, swift-concurrency-pro, swift-testing-pro]
---

# SwiftData Pro

An agent skill from Paul Hudson (twostraws) that writes, reviews, and improves SwiftData code using modern APIs and best practices.

## Overview

Source: [twostraws/SwiftData-Agent-Skill](https://github.com/twostraws/SwiftData-Agent-Skill)

Installed in `.agents/skills/swiftdata-pro/` as part of the four twostraws agent skills.

## What It Covers

- **@Model** — Core SwiftData model declaration
- **@Query** — Querying SwiftData (only inside SwiftUI views)
- **Predicates** — Safe predicate operations
- **Indexes** — Indexing for performance
- **Migrations** — Model migrations
- **Relationships** — @Relationship with cascade delete
- **iCloud** — CloudKit integration
- **Class inheritance** — iOS 26+ patterns

## Key Rules

- Target Swift 6.2 or later, using modern Swift concurrency
- The user strongly prefers to use SwiftData across the board
- Do not suggest Core Data unless it's a feature that cannot be solved with SwiftData
- Do not introduce third-party frameworks without asking first
- Use a consistent project structure, with folder layout determined by app features
- **@Query must only be used inside SwiftUI views** — not in classes
- **isEmpty == false crashes at runtime** — use !isEmpty instead
- iOS 26+ class inheritance patterns
- CloudKit-specific constraints (uniqueness, optionality, eventual consistency)
- Add explicit delete rules for relationships: `@Relationship(deleteRule: .cascade, inverse: \Sight.destination)`

## How It Works

The skill loads its `SKILL.md` and `references/` directory on demand during code review. It checks:
1. Core SwiftData issues (using `references/core-rules.md`)
2. Predicates are safe and supported (using `references/predicates.md`)
3. CloudKit-specific constraints (using `references/cloudkit.md`)
4. Indexing opportunities (using `references/indexing.md`)
5. Class inheritance patterns (using `references/class-inheritance.md`)

## Installation

```bash
npx skills add https://github.com/twostraws/SwiftData-Agent-Skill --skill swiftdata-pro
```

## See Also

- [[swiftui-pro]]
- [[swift-concurrency-pro]]
- [[swift-testing-pro]]
- [[ui-ux-design]]
- [[agent-skills]]
