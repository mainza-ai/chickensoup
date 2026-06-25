---
created: 2026-06-22
protected: true
related:
- swiftui-pro
- swiftdata-pro
- swift-concurrency-pro
sources:
- twostraws-swift-testing-pro-2026
tags:
- swift
- testing
- agent-skill
- twostraws
title: Swift Testing Pro
updated: '2026-06-25'
---

# Swift Testing Pro

An agent skill from Paul Hudson (twostraws) that writes, reviews, and improves Swift Testing code using modern APIs and best practices.

## Overview

Source: [twostraws/Swift-Testing-Agent-Skill](https://github.com/twostraws/Swift-Testing-Agent-Skill)

Installed in `.agents/skills/swift-testing-pro/` as part of the four twostraws agent skills.

## What It Covers

- **@Test** — Test function declaration
- **#expect** — Expectations
- **#require** — Preconditions (safely unwraps)
- **Parameterized tests** — Test with multiple inputs
- **Traits** — Test traits for filtering
- **Exit tests** — Test program exits
- **Confirmations** — Test multiple occurrences
- **Parallel execution** — Tests run in parallel
- **Async tests** — Async/await in tests

## Key Rules

- Target Swift 6.2 or later with modern Swift concurrency
- **Swift Testing does NOT support UI tests** — use XCTest for UI tests
- Use **struct, not class**, for test suites
- Use **#expect** for expectations, **#require** for preconditions
- **init/deinit** over setUp/tearDown
- **Parallel execution** is the default
- Use raw identifiers for test names
- Use range-based confirmations
- Use test scoping traits
- Use exit tests for testing program exits
- Use attachments for test attachments
- Use #require(throws:) for exception testing
- Floating-point tolerance via Swift Numerics

## How It Works

The skill loads its `SKILL.md` and `references/` directory on demand during code review. It checks:
1. Core Swift Testing conventions (using `references/core-rules.md`)
2. Test structure, assertions, dependency injection (using `references/writing-better-tests.md`)
3. Async tests, confirmations, time limits, actor isolation (using `references/async-tests.md`)
4. New features like raw identifiers, test scopes, exit tests (using `references/new-features.md`)
5. XCTest to Swift Testing conversion (using `references/migrating-from-xctest.md`)

## Installation

```bash
npx skills add https://github.com/twostraws/Swift-Testing-Agent-Skill --skill swift-testing-pro
```

## See Also

- [[swiftui-pro]]
- [[swiftdata-pro]]
- [[swift-concurrency-pro]]
- [[ui-ux-design]]
- [[agent-skills]]

