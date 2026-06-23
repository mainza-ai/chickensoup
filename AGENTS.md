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
```

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

### Lint Checklist

- [ ] Contradictions between pages
- [ ] Stale claims superseded by newer sources
- [ ] Orphan pages with no inbound links
- [ ] Important concepts without their own page
- [ ] Missing cross-references
- [ ] Data gaps
