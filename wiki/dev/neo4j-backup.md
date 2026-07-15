---
title: "Neo4j Backup & Restore"
tags: [neo4j, backup, restore, database, devops, infrastructure]
created: 2026-07-15
updated: 2026-07-15
sources: []
related: [neo4j, docker, backup-restore, project-structure]
---

# Neo4j Backup & Restore

Automatic database dump system using `neo4j-admin database dump`. Creates portable dump files that can be distributed for fresh clones — no need to re-ingest 637 pages.

## Architecture

`src/neo4j_backup.py` manages the lifecycle:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scheduler  │────→│  Backup Loop │────→│  create_backup() │
│  (24h)      │     │  (async)     │     │  │
└─────────────┘     └──────────────┘     │  ├── docker stop neo4j
                                          │  ├── neo4j-admin database dump
                                          │  ├── docker start neo4j
                                          │  └── cleanup_old_backups()
                                          │
                              ┌───────────▼─────────┐
                              │  backups/neo4j/     │
                              │  neo4j-dump-*.dump   │
                              └─────────────────────┘
```

Since Neo4j Community edition requires the database to be offline for `neo4j-admin database dump`, the backup function:
1. Stops the Docker container (30s timeout)
2. Mounts the same data volume into a temporary container
3. Runs `neo4j-admin database dump` 
4. Starts the container
5. Waits for Neo4j to become ready (up to 60s)
6. Cleans up backups older than retention period

Total downtime: ~30-60 seconds per backup.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/neo4j/backup` | Trigger immediate backup |
| `GET` | `/neo4j/backups` | List available dump files |
| `POST` | `/neo4j/restore/{dump_name}` | Restore from dump file |

## Configuration (in `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_BACKUP_ENABLED` | `true` | Master switch for backup scheduler |
| `NEO4J_BACKUP_DIR` | `backups/neo4j` | Where dump files are stored |
| `NEO4J_BACKUP_RETENTION_DAYS` | `30` | Auto-delete backups older than this |
| `NEO4J_BACKUP_INTERVAL_HOURS` | `24` | How often to run the backup |
| `NEO4J_URI_HOST_DATA` | `/var/lib/docker/volumes/.../_data` | Host path to Neo4j data volume (needs to match `docker-compose.yml`) |

## Fresh Clone Flow

For new users cloning the repo:

1. Run `docker compose up -d neo4j redis` (or just start Neo4j however you prefer)
2. Place a dump file in `backups/neo4j/`
3. `curl -X POST http://localhost:8000/neo4j/restore/neo4j-dump-2026-07-15.dump`
4. Server starts with full graph — no 3-hour reconciliation needed

## See Also

- [[neo4j]]
- [[docker]]
- [[backup-restore]]
- [[project-structure]]
