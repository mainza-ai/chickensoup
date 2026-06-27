---
title: "Wiki Backup & Restore"
tags: [wiki, backup, restore, export, import]
created: 2026-06-26
updated: 2026-06-26
sources: [wiki-backup]
related: [wiki-file-system, wiki-cleanup, ingestion-pipeline, redis]
---

# Wiki Backup & Restore

Wiki backup and restore functionality for creating, importing, and managing markdown vault snapshots. Implementation in `src/wiki/backup.py` (180 lines).

## Overview

The backup system creates ZIP archives of the entire wiki directory (excluding backup directories) and stores them in a separate backup location. It supports both automatic snapshots and manual exports, plus import/restore from ZIP files.

## Directory Structure

```
wiki/
├── entities/          ← Main wiki content
├── concepts/
├── projects/
├── raw/
├── log.md
├── index.md
└── backups/           ← Backup storage (gitignored)
    ├── auto/          ← Automatic snapshots
    └── manual/        ← Manual exports
```

The backup directory is controlled by `WIKI_BACKUP_DIR` in settings. By default it is `wiki/backups/`.

## Functions

### `create_snapshot(name="auto")` → `str | None`

Creates a timestamped ZIP snapshot of the wiki.

- **Parameters:** `name` — "auto" for automatic backups, any other string for manual
- **Output:** Full path to the ZIP file, or `None` if backups are disabled
- **Guard:** Skipped if `WIKI_BACKUP_ENABLED` is `False`
- **Excludes:** The backup directory itself from the archive (avoids circular inclusion)
- **Storage:** `backups/auto/wiki-{timestamp}.zip` or `backups/{name}/wiki-{timestamp}.zip`

### `export_wiki()` → `str | None`

Creates a manual export ZIP. Same logic as `create_snapshot` but always stores in `backups/manual/`.

### `import_wiki(zip_path: str)` → `int`

Restores wiki pages from a ZIP file.

- **Parameters:** `zip_path` — Path to the ZIP file to import
- **Output:** Number of pages restored, or `0` on failure
- **Validation:** Checks that the ZIP contains a `wiki/` directory with `entities/`, `concepts/`, or `projects/` subdirectories
- **Restoration:** Copies `.md` files from each subdirectory, preserving filenames
- **Cache invalidation:** Clears the wiki index cache and all Redis caches after import
- **Cleanup:** Removes the temporary extraction directory in `finally` block

### `cleanup_old_backups(retention_days=None)` → `int`

Removes backups older than the configured retention period.

- **Parameters:** `retention_days` — Overrides `WIKI_BACKUP_RETENTION_DAYS` from settings
- **Scans:** Both `backups/auto/` and `backups/manual/`
- **Returns:** Number of files deleted

### `list_backups(subdir="auto")` → `list[dict]`

Lists available backups in a subdirectory.

- **Returns:** List of dicts with `filename`, `path`, `created` (ISO 8601), `size_kb`
- **Order:** Most recent first

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `WIKI_BACKUP_ENABLED` | (env var) | Master switch for backup creation |
| `WIKI_BACKUP_DIR` | `wiki/backups` | Backup storage directory |
| `WIKI_BACKUP_RETENTION_DAYS` | (env var) | Days to keep auto backups before cleanup |

## Integration Points

- **Wiki cleanup** — `clear_content_pages()` calls `create_snapshot()` before deleting pages (dry_run mode skips the snapshot)
- **Cache invalidation** — Import invalidates both the wiki index cache (in-memory) and all Redis caches
- **Logging** — All operations logged via `chickensoup.wiki.backup` logger

## See Also

- [[wiki-file-system]] — Markdown wiki vault structure
- [[wiki-cleanup]] — Content deletion with protection rules
- [[redis]] — Caching layer for wiki index
