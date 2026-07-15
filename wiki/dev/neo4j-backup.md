---
title: "Neo4j Backup & Restore"
tags: [neo4j, backup, restore, database, devops, infrastructure]
created: 2026-07-15
updated: 2026-07-15
sources: []
related: [neo4j, docker, backup-restore, project-structure]
---

# Neo4j Backup & Restore

Automatic database dump system using `neo4j-admin database dump`. Creates portable dump files stored via Git LFS for distribution to fresh clones — no need to re-ingest 525+ wiki pages.

## Architecture

`src/neo4j_backup.py` manages the lifecycle:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Scheduler  │────→│  Backup Loop │────→│  create_backup() │
│  (24h)      │     │  (async)     │     │  │
└─────────────┘     └──────────────┘     │  ├── docker stop
                                          │  ├── neo4j-admin dump
                                          │  ├── docker start
                                          │  └── cleanup old
                                          │
                              ┌───────────▼──────────┐
                              │  backups/neo4j/       │
                              │  ├── seed.dump (LFS)  │
                              │  └── neo4j-dump-*.dump│
                              └───────────────────────┘
                              ↕ Git LFS track
                              GitHub storage
```

Since Neo4j Community edition requires the database to be offline for `neo4j-admin database dump`, the backup function:
1. Stops the Docker container (30s timeout)
2. Resolves the data volume by name (`chickensoup_neo4j_data`)
3. Runs `neo4j-admin database dump` in a temporary container
4. Starts the container
5. Waits for Neo4j to become ready (up to 60s)
6. Cleans up backups older than retention period

Total downtime: ~30-60 seconds per backup.

## Auto-Restore on Startup

`main.py` checks at startup: if Neo4j is empty and `backups/neo4j/seed.dump` exists, it automatically restores from the seed dump before the server starts. The seed dump is tracked via Git LFS so new clones get it with `git lfs pull`.

**Fresh clone flow — zero manual steps:**
```bash
git clone https://github.com/mainza-ai/chickensoup.git
cd chickensoup
git lfs pull              # downloads 11MB seed.dump
docker compose up -d      # starts Neo4j (empty)
uv run uvicorn src.main:app  # auto-restores seed → full graph instantly
```

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/neo4j/backup` | Yes | Trigger immediate backup |
| `GET` | `/neo4j/backups` | No | List available dump files |
| `POST` | `/neo4j/restore/{dump_name}` | Yes | Restore from dump file |

## Configuration (in `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_BACKUP_ENABLED` | `true` | Master switch for backup scheduler |
| `NEO4J_BACKUP_DIR` | `backups/neo4j` | Where dump files are stored |
| `NEO4J_BACKUP_RETENTION_DAYS` | `30` | Auto-delete backups older than this |
| `NEO4J_BACKUP_INTERVAL_HOURS` | `24` | How often to run the backup |
| `NEO4J_CONTAINER_NAME` | `chickensoup-neo4j` | Docker container name |
| `NEO4J_DATA_VOLUME` | `chickensoup_neo4j_data` | Docker volume for data |

## Regenerating the Seed Dump

When the wiki content changes significantly (new pages, updated relationships):

```bash
curl -X POST http://localhost:8000/neo4j/backup
cp backups/neo4j/neo4j-dump-*.dump backups/neo4j/seed.dump
git add backups/neo4j/seed.dump
git commit -m "Update seed dump"
git push
```

The seed dump is only ~11MB (525 nodes, 5762 relationships). Git LFS keeps it out of the main repo history.

## See Also

- [[neo4j]]
- [[docker]]
- [[backup-restore]]
- [[project-structure]]
