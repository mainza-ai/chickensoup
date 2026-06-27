import logging
import os
import yaml
from datetime import date
from typing import Dict, List, Set, Tuple

from src.config import settings
from src.wiki.writer import invalidate_index_cache
from src.cache import cache_store

logger = logging.getLogger("chickensoup.wiki.cleanup")

WIKI_DIR = settings.WIKI_DATA_DIR
if not os.path.isabs(WIKI_DIR):
    WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), WIKI_DIR)

SUBDIRS = ["entities", "concepts", "projects"]

ENGINEERING_TAGS: Set[str] = {
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

CONTENT_TAGS: Set[str] = {
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


def _page_path(page_type: str, slug: str) -> str:
    return os.path.join(WIKI_DIR, page_type, f"{slug}.md")


def _read_page_frontmatter(filepath: str) -> Tuple[dict, str]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    meta = {}
    body = content
    import re
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if yaml_match:
        try:
            meta = yaml.safe_load(yaml_match.group(1)) or {}
        except Exception:
            pass
        body = content[yaml_match.end():]
    return meta, body


def _write_page_frontmatter(filepath: str, frontmatter: dict, body: str):
    frontmatter["updated"] = date.today().isoformat()
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---\n{yaml_str}\n---\n\n{body}\n")


def _should_preserve(frontmatter: dict, page_type: str, filename: str) -> bool:
    if frontmatter.get("protected", False):
        return True

    if page_type == "projects":
        return True

    if filename == "primary-researcher.md":
        return True

    tags = set(frontmatter.get("tags", []))

    if tags & ENGINEERING_TAGS:
        return True

    if tags & CONTENT_TAGS:
        return False

    if page_type in ("entities", "concepts"):
        return False

    return True


def clear_content_pages(dry_run: bool = True) -> dict:
    preserved_slugs: List[str] = []
    deleted_slugs: List[str] = []
    protected_added: List[str] = []

    if not dry_run:
        from src.wiki.backup import create_snapshot
        snapshot_path = create_snapshot()
        if snapshot_path:
            logger.info(f"Pre-clear snapshot saved: {snapshot_path}")
        else:
            logger.warning("Pre-clear snapshot could not be created — proceeding anyway")

    for subdir in SUBDIRS:
        dir_path = os.path.join(WIKI_DIR, subdir)
        if not os.path.isdir(dir_path):
            continue

        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith(".md"):
                continue

            slug = fname[:-3]
            filepath = os.path.join(dir_path, fname)
            frontmatter, body = _read_page_frontmatter(filepath)

            preserve = _should_preserve(frontmatter, subdir, fname)

            if preserve:
                if not frontmatter.get("protected", False) and frontmatter.get("tags"):
                    protected_added.append(f"{subdir}/{slug}")
                    if not dry_run:
                        frontmatter["protected"] = True
                        _write_page_frontmatter(filepath, frontmatter, body)
                        logger.info(f"Added protected flag to {subdir}/{slug}")
                    else:
                        logger.info(f"[DRY RUN] Would add protected flag to {subdir}/{slug}")
                preserved_slugs.append(f"{subdir}/{slug}")
            else:
                deleted_slugs.append(f"{subdir}/{slug}")
                if not dry_run:
                    try:
                        os.remove(filepath)
                        logger.info(f"Deleted content page: {subdir}/{slug}")
                    except Exception as e:
                        logger.error(f"Failed to delete {filepath}: {e}")
                else:
                    logger.info(f"[DRY RUN] Would delete content page: {subdir}/{slug}")

    if not dry_run:
        _rebuild_index(preserved_slugs)
        _append_to_log(
            f"Wiki content clear: {len(preserved_slugs)} preserved, "
            f"{len(deleted_slugs)} deleted, "
            f"{len(protected_added)} pages flagged as protected"
        )
        invalidate_index_cache()
        cache_store.invalidate_all()
        logger.info(f"Wiki clear complete: {len(preserved_slugs)} preserved, {len(deleted_slugs)} deleted")
    else:
        logger.info(f"[DRY RUN] Wiki clear preview: {len(preserved_slugs)} preserved, {len(deleted_slugs)} deleted")

    return {
        "success": True,
        "dry_run": dry_run,
        "preserved_count": len(preserved_slugs),
        "deleted_count": len(deleted_slugs),
        "protected_added_count": len(protected_added),
        "preserved_slugs": preserved_slugs,
        "deleted_slugs": deleted_slugs,
    }


def _rebuild_index(preserved_slugs: List[str]):
    index_path = os.path.join(WIKI_DIR, "index.md")
    if not os.path.isfile(index_path):
        return

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    yaml_match = re.match(r"^(---\s*\n.*?\n---)\s*\n", content, re.DOTALL)
    if not yaml_match:
        return

    header = yaml_match.group(1) + "\n\n"
    existing_body = content[yaml_match.end():]

    sections = {"Entities": [], "Concepts (in wiki/concepts/)": [], "Projects (in wiki/projects/)": []}
    current_section = "Entities"
    for line in existing_body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            section_name = stripped[3:]
            if section_name in sections:
                current_section = section_name
            continue
        if stripped.startswith("- [[") and "]]" in stripped:
            link_name = stripped[stripped.index("[[") + 2 : stripped.index("]]")]
            slug = link_name.lower().replace(" ", "-").replace("_", "-")
            page_type = "entities"
            if current_section == "Concepts (in wiki/concepts/)":
                page_type = "concepts"
            elif current_section == "Projects (in wiki/projects/)":
                page_type = "projects"
            if f"{page_type}/{slug}" in preserved_slugs or any(
                s.endswith(f"/{slug}") for s in preserved_slugs
            ):
                sections.setdefault(current_section, []).append(line)

    body_parts = []
    for section_name in ["Entities", "Concepts (in wiki/concepts/)", "Projects (in wiki/projects/)"]:
        entries = sections.get(section_name, [])
        if entries:
            body_parts.append(f"## {section_name}\n")
            for entry in entries:
                body_parts.append(f"{entry}\n")
            body_parts.append("\n")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(header + "".join(body_parts))

    logger.info("Index rebuilt after wiki content clear")


def _append_to_log(entry_text: str):
    log_path = os.path.join(WIKI_DIR, "log.md")
    if not os.path.isfile(log_path):
        return

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    yaml_match = re.match(r"^(---\s*\n.*?\n---)\s*\n", content, re.DOTALL)
    if not yaml_match:
        return

    header = yaml_match.group(1) + "\n\n"
    body = content[yaml_match.end():]

    today = date.today().isoformat()
    log_entry = f"\n## [{today}] cleanup | {entry_text}\n"
    body = body.rstrip() + log_entry + "\n"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(header + body)
