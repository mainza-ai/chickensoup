---
title: "Wiki Cleanup"
tags: [wiki, cleanup, deletion, protection]
created: 2026-06-26
updated: 2026-06-26
sources: [wiki-cleanup]
related: [wiki-file-system, wiki-backup-restore, ingestion-pipeline, redis]
---

# Wiki Cleanup

Wiki cleanup functionality for bulk-deleting content pages while preserving engineering and protected pages. Implementation in `src/wiki/cleanup.py` (251 lines).

## Overview

The cleanup system classifies wiki pages into **preserved** (engineering metadata, protected pages) and **deletable** (UFO/alien/time-travel content). It is designed to reset the knowledge base to a clean state while keeping the structural/engineering pages intact.

## Page Classification

Pages are classified using a tag-based heuristic system. Two tag sets define the classification criteria:

### Engineering Tags (Always Preserved)

```python
ENGINEERING_TAGS = {
    "agent", "api", "architecture", "automation", "batch", "build", "cache",
    "celery", "ci-cd", "configuration", "consensus", "container", "crud",
    "database", "decisions", "design", "devops", "discovery", "docker",
    "endpoints", "evaluation", "fallback", "fastapi", "fastmcp", "files",
    "framework", "frontend", "frontmatter", "github", "graph",
    "hardware", "infrastructure", "ingest", "integration",
    "knowledge-graph", "langgraph", "liquid-glass", "llm", "local",
    "logging", "markdown", "mcp", "metrics", "models", "monitoring",
    "multi-llm", "neo4j", "observability", "omx", "orchestration",
    "organization", "person", "production", "project", "pydantic",
    "pyproject", "pytest", "python", "quantum", "readiness", "reasoning",
    "redis", "reliability", "resilience", "schema", "scheduler",
    "scheduling", "settings", "simulation", "skills", "stack",
    "structure", "swift", "swiftdata", "swiftui", "technology",
    "temporal", "testing", "tools", "tracing", "tql", "twostraws",
    "ui", "upload", "user", "ux", "wiki", "workflows",
}
```

### Content Tags (Deletable)

```python
CONTENT_TAGS = {
    "alien", "antigravity", "ascension", "bible", "brain",
    "consciousness", "cosmology", "crash", "death-ray", "disclosure",
    "earth", "electrogravitics", "elohim", "entanglement", "entropy",
    "evidence", "frequency", "giants", "gravity", "hearing",
    "incident", "intelligence", "inventions", "meditation",
    "military", "nephilim", "neuroscience", "particle-beam",
    "philosophy", "prophet", "propulsion", "religion", "remote-viewing",
    "retrieval", "retrocausality", "schumann-resonance", "sighting",
    "simulation", "spacetime", "tesla", "testimonies",
    "thermodynamics", "time-travel", "ufo", "uap",
    "vision", "weapon", "whistleblower", "wireless-energy", "witnesses",
}
```

### Classification Logic

1. If page has `protected: true` in frontmatter → **preserved**
2. If page is in `projects/` → **preserved** (all engineering docs)
3. If page is `primary-researcher.md` → **preserved** (user entity)
4. If page has any `ENGINEERING_TAGS` → **preserved**
5. If page has any `CONTENT_TAGS` → **deletable**
6. If page is in `entities/` or `concepts/` with no matching tags → **deletable**
7. Otherwise → **preserved**

## Clear Content Pages

`clear_content_pages(dry_run=True)` → `dict`

The main cleanup function. Iterates all `.md` files in `entities/`, `concepts/`, and `projects/`.

### Dry Run Mode (Default)

- Scans all pages and classifies them
- Identifies content pages that would be deleted
- Identifies engineering pages that would be flagged as `protected: true`
- Returns classification results without modifying any files
- Logs `[DRY RUN]` prefixed messages

### Execute Mode (`dry_run=False`)

1. **Pre-clear snapshot** — Calls `create_snapshot()` to save a backup before deletion
2. **Classify pages** — Same as dry run
3. **Flag protected pages** — Pages that match engineering tags but lack `protected: true` get the flag set in their frontmatter
4. **Delete content pages** — Removes `.md` files for pages classified as deletable
5. **Rebuild index** — Rebuilds `wiki/index.md` with only preserved pages
6. **Append to log** — Records the cleanup event in `wiki/log.md`
7. **Invalidate caches** — Clears wiki index cache and all Redis caches

### Return Value

```python
{
    "success": True,
    "dry_run": bool,
    "preserved_count": int,
    "deleted_count": int,
    "protected_added_count": int,
    "preserved_slugs": List[str],    # e.g., ["entities/neo4j.md", "concepts/api-design.md"]
    "deleted_slugs": List[str],       # e.g., ["entities/roswell-crash.md"]
}
```

## Index Rebuild

After deletion, `wiki/index.md` is rebuilt by:
1. Parsing the YAML frontmatter header
2. Scanning existing entries under each section (Entities, Concepts, Projects)
3. For each entry, checking if the corresponding page file still exists
4. Writing only entries for preserved pages

## Log Entry Format

Cleanup events are appended to `wiki/log.md` with the format:

```markdown
## [2026-06-26] cleanup | Wiki content clear: 45 preserved, 33 deleted, 12 pages flagged as protected
```

## See Also

- [[wiki-file-system]] — Markdown wiki vault structure
- [[wiki-backup-restore]] — Backup and import functionality
- [[redis]] — Caching layer for wiki index
