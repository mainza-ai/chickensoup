import datetime
import logging
import os
import shutil
import tempfile
import zipfile
from typing import Optional

from src.config import settings

logger = logging.getLogger("chickensoup.wiki.backup")

WIKI_DIR = settings.WIKI_DATA_DIR
if not os.path.isabs(WIKI_DIR):
    WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), WIKI_DIR)

BACKUP_DIR = settings.WIKI_BACKUP_DIR
if not os.path.isabs(BACKUP_DIR):
    BACKUP_DIR = os.path.join(WIKI_DIR, BACKUP_DIR)


def _ensure_backup_dir():
    os.makedirs(os.path.join(BACKUP_DIR, "auto"), exist_ok=True)
    os.makedirs(os.path.join(BACKUP_DIR, "manual"), exist_ok=True)


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")


def create_snapshot(name: str = "auto") -> Optional[str]:
    if not settings.WIKI_BACKUP_ENABLED:
        logger.info("Wiki backups are disabled — skipping snapshot")
        return None

    _ensure_backup_dir()
    subdir = "auto" if name == "auto" else name
    subdir_path = os.path.join(BACKUP_DIR, subdir)
    os.makedirs(subdir_path, exist_ok=True)
    ts = _timestamp()
    filename = f"wiki-{ts}.zip"
    filepath = os.path.join(BACKUP_DIR, subdir, filename)

    try:
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(WIKI_DIR):
                if os.path.abspath(root) == os.path.abspath(BACKUP_DIR) or os.path.abspath(root).startswith(os.path.abspath(BACKUP_DIR) + os.sep):
                    dirs[:] = []
                    continue
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(full_path, os.path.dirname(WIKI_DIR))
                    zf.write(full_path, arcname)

        size_kb = os.path.getsize(filepath) / 1024
        logger.info(f"Wiki snapshot created: {filepath} ({size_kb:.1f} KB)")
        return filepath
    except Exception as e:
        logger.error(f"Failed to create wiki snapshot: {e}")
        return None


def export_wiki() -> Optional[str]:
    _ensure_backup_dir()
    ts = _timestamp()
    filename = f"wiki-export-{ts}.zip"
    filepath = os.path.join(BACKUP_DIR, "manual", filename)

    try:
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(WIKI_DIR):
                if os.path.abspath(root) == os.path.abspath(BACKUP_DIR) or os.path.abspath(root).startswith(os.path.abspath(BACKUP_DIR) + os.sep):
                    dirs[:] = []
                    continue
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(full_path, os.path.dirname(WIKI_DIR))
                    zf.write(full_path, arcname)

        size_kb = os.path.getsize(filepath) / 1024
        logger.info(f"Wiki export created: {filepath} ({size_kb:.1f} KB)")
        return filepath
    except Exception as e:
        logger.error(f"Failed to export wiki: {e}")
        return None


def import_wiki(zip_path: str) -> int:
    restored_count = 0
    temp_dir = tempfile.mkdtemp(prefix="wiki_import_")

    try:
        logger.info(f"Starting wiki import from {zip_path}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        extracted_wiki = os.path.join(temp_dir, "wiki")
        if not os.path.isdir(extracted_wiki):
            extracted_wiki = temp_dir
            wiki_subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if not any(s in wiki_subdirs for s in ["entities", "concepts", "projects"]):
                logger.error("Import zip does not contain a valid wiki directory structure")
                shutil.rmtree(temp_dir)
                return 0

        for subdir in ["entities", "concepts", "projects"]:
            src_dir = os.path.join(extracted_wiki, subdir)
            dst_dir = os.path.join(WIKI_DIR, subdir)
            if not os.path.isdir(src_dir):
                continue
            os.makedirs(dst_dir, exist_ok=True)
            for fname in os.listdir(src_dir):
                if not fname.endswith(".md"):
                    continue
                src_file = os.path.join(src_dir, fname)
                dst_file = os.path.join(dst_dir, fname)
                shutil.copy2(src_file, dst_file)
                restored_count += 1

        from src.wiki.writer import invalidate_index_cache
        invalidate_index_cache()

        from src.cache import cache_store
        cache_store.invalidate_all()

        logger.info(f"Wiki import complete: {restored_count} pages restored from {zip_path}")
        return restored_count
    except Exception as e:
        logger.error(f"Failed to import wiki: {e}")
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def cleanup_old_backups(retention_days: Optional[int] = None):
    if retention_days is None:
        retention_days = settings.WIKI_BACKUP_RETENTION_DAYS

    cutoff = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    cleaned = 0

    for subdir in ["auto", "manual"]:
        dir_path = os.path.join(BACKUP_DIR, subdir)
        if not os.path.isdir(dir_path):
            continue
        for fname in os.listdir(dir_path):
            if not fname.endswith(".zip"):
                continue
            filepath = os.path.join(dir_path, fname)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                try:
                    os.remove(filepath)
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {filepath}: {e}")

    if cleaned:
        logger.info(f"Cleaned {cleaned} old backup(s) older than {retention_days} days")


def list_backups(subdir: str = "auto") -> list:
    dir_path = os.path.join(BACKUP_DIR, subdir)
    if not os.path.isdir(dir_path):
        return []

    backups = []
    for fname in sorted(os.listdir(dir_path), reverse=True):
        if not fname.endswith(".zip"):
            continue
        filepath = os.path.join(dir_path, fname)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
        size_kb = os.path.getsize(filepath) / 1024
        backups.append({
            "filename": fname,
            "path": filepath,
            "created": mtime.isoformat(),
            "size_kb": round(size_kb, 1),
        })
    return backups
