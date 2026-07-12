import os
import shutil
import logging
import yaml
from typing import List, Dict, Any, Optional

from src.config import settings
from src.wiki.writer import _page_path, read_page, slugify, invalidate_index_cache

logger = logging.getLogger("chickensoup.discovery_agent")

DRAFT_DIR = os.path.join(settings.WIKI_DATA_DIR, "raw", "drafts")

def get_draft_path(slug: str) -> str:
    return os.path.join(DRAFT_DIR, f"{slug}.md")

def is_draft(slug: str) -> bool:
    return os.path.isfile(get_draft_path(slug))

def list_drafts() -> List[Dict[str, Any]]:
    """Lists all currently proposed draft entities."""
    if not os.path.isdir(DRAFT_DIR):
        return []
    
    drafts = []
    for filename in os.listdir(DRAFT_DIR):
        if filename.endswith(".md"):
            slug = filename[:-3]
            path = os.path.join(DRAFT_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Basic frontmatter parsing
                meta = {}
                import re
                yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                if yaml_match:
                    meta = yaml.safe_load(yaml_match.group(1)) or {}
                drafts.append({
                    "slug": slug,
                    "title": meta.get("title", slug),
                    "created": meta.get("created"),
                    "updated": meta.get("updated"),
                    "tags": meta.get("tags", []),
                    "path": path
                })
            except Exception as e:
                logger.warning(f"Failed to parse draft {filename}: {e}")
    return drafts

def promote_draft(slug: str) -> bool:
    """Promotes a draft entity to the published wiki/entities/ directory."""
    draft_path = get_draft_path(slug)
    if not os.path.isfile(draft_path):
        logger.warning(f"Draft '{slug}' not found for promotion")
        return False
        
    dest_path = _page_path(slug, "entities")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    try:
        shutil.move(draft_path, dest_path)
        logger.info(f"Promoted draft '{slug}' to published entities: {dest_path}")
        
        # Rebuild/append index and cache
        from src.wiki.writer import append_to_index, read_page
        display_name = slug
        page_data = read_page(slug, "entities")
        if page_data and "frontmatter" in page_data:
            display_name = page_data["frontmatter"].get("title", slug)
        append_to_index([(slug, display_name, "entities")])
        invalidate_index_cache()
        
        # Add to staleness queue
        from src.staleness_queue import record_pulse_completed
        record_pulse_completed(slug)
        
        return True
    except Exception as e:
        logger.error(f"Failed to promote draft '{slug}': {e}", exc_info=True)
        return False
