"""Neo4j database backup and restore via neo4j-admin database dump.

Runs neo4j-admin inside the Docker container, handling stop/start around
the dump (required for Community edition). Backup files are portable —
can be restored by any Neo4j 5.x instance.
"""
import os
import re
import json
import glob
import time
import shutil
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pathlib import Path
from src.config import settings

logger = logging.getLogger("chickensoup.neo4j_backup")

BACKUP_DIR = Path(settings.NEO4J_BACKUP_DIR)
RETENTION_DAYS = settings.NEO4J_BACKUP_RETENTION_DAYS
CONTAINER_NAME = getattr(settings, "NEO4J_CONTAINER_NAME", "neo4j")
NEO4J_DB_NAME = "neo4j"
BACKUP_VOLUME_NAME = getattr(settings, "NEO4J_DATA_VOLUME", "chickensoup_neo4j_data")


def _get_data_volume() -> str:
    """Resolve the data volume mount from the running container, or fall back to configured name."""
    try:
        result = subprocess.run(
            ["docker", "inspect", CONTAINER_NAME, "--format",
             "{{range .Mounts}}{{if eq .Destination \"/data\"}}{{.Name}}{{end}}{{end}}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return BACKUP_VOLUME_NAME


def _container_running() -> bool:
    result = subprocess.run(
        ["docker", "container", "inspect", CONTAINER_NAME, "--format", "{{.State.Running}}"],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _start_container():
    logger.info("Starting Neo4j container...")
    subprocess.run(
        ["docker", "start", CONTAINER_NAME],
        capture_output=True, text=True, timeout=30, check=True,
    )
    # Wait for Neo4j to be ready
    for _ in range(30):
        try:
            result = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "cypher-shell", "-u", settings.NEO4J_USER,
                 "-p", settings.NEO4J_PASSWORD, "RETURN 1"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                logger.info("Neo4j container ready")
                return True
        except Exception:
            pass
        time.sleep(2)
    logger.error("Neo4j container did not become ready within 60s")
    return False


def _stop_container():
    logger.info("Stopping Neo4j container for backup...")
    subprocess.run(
        ["docker", "stop", "--time", "30", CONTAINER_NAME],
        capture_output=True, text=True, timeout=60, check=True,
    )
    logger.info("Neo4j container stopped")


def _run_dump(dump_path: Path) -> bool:
    logger.info(f"Running neo4j-admin database dump to {dump_path}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    volume = _get_data_volume()
    try:
        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{volume}:/data",
             "-v", f"{os.path.abspath(BACKUP_DIR)}:/backups",
             "neo4j:5.18.0",
             "neo4j-admin", "database", "dump", NEO4J_DB_NAME,
             "--to-path=/backups"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            logger.info(f"Dump succeeded: {dump_path}")
            return True
        else:
            logger.error(f"Dump failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Dump timed out after 300s")
        return False
    except FileNotFoundError:
        logger.error("Docker not found — cannot run neo4j-admin dump")
        return False


def _run_restore(dump_path: Path) -> bool:
    logger.info(f"Restoring from {dump_path}")
    volume = _get_data_volume()
    try:
        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{volume}:/data",
             "-v", f"{os.path.abspath(dump_path.parent)}:/backups",
             "neo4j:5.18.0",
             "neo4j-admin", "database", "load", NEO4J_DB_NAME,
             "--from-path=/backups", "--force"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            logger.info("Restore succeeded")
            return True
        else:
            logger.error(f"Restore failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Restore timed out after 300s")
        return False
    except FileNotFoundError:
        logger.error("Docker not found — cannot run restore")
        return False


def create_backup() -> Optional[Path]:
    """Create a Neo4j database dump. Stops container, dumps, restarts.
    Returns path to the dump file, or None on failure."""
    if not _container_running():
        logger.error("Neo4j container is not running")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    dump_name = f"neo4j-dump-{timestamp}.dump"
    dump_path = BACKUP_DIR / dump_name

    was_running = _container_running()
    try:
        if was_running:
            _stop_container()
        if _run_dump(dump_path):
            return dump_path
        return None
    finally:
        if was_running:
            _start_container()


def restore_backup(dump_name: str) -> bool:
    """Restore Neo4j from a dump file. Stops container, loads, restarts."""
    dump_path = BACKUP_DIR / dump_name
    if not dump_path.exists():
        logger.error(f"Backup file not found: {dump_path}")
        return False

    was_running = _container_running()
    try:
        if was_running:
            _stop_container()
        if _run_restore(dump_path):
            return True
        return False
    finally:
        if was_running:
            _start_container()


def list_backups() -> List[dict]:
    """List available backup dump files with metadata."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for f in sorted(BACKUP_DIR.glob("neo4j-dump-*.dump"), reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return backups


def cleanup_old_backups() -> int:
    """Remove backup files older than RETENTION_DAYS. Returns count deleted."""
    if not BACKUP_DIR.exists():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    deleted = 0
    for f in BACKUP_DIR.glob("neo4j-dump-*.dump"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            f.unlink()
            deleted += 1
            logger.info(f"Deleted old backup: {f.name}")
    return deleted


def _human_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}TB"
