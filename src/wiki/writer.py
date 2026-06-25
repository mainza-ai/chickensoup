import os
import re
import logging
from datetime import date
from typing import Optional, Dict, Any, List, Tuple
import yaml

logger = logging.getLogger("chickensoup.wiki.writer")

WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "wiki")
SUBDIRS = {
    "entities": "entities",
    "concepts": "concepts",
    "projects": "projects",
}

def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-").replace("/", "-")

def _page_path(slug: str, page_type: str = "entities") -> str:
    return os.path.join(WIKI_DIR, page_type, f"{slug}.md")

def read_page(slug: str, page_type: str = "entities") -> Optional[Dict[str, Any]]:
    path = _page_path(slug, page_type)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    meta = {}
    body = content
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if yaml_match:
        try:
            meta = yaml.safe_load(yaml_match.group(1)) or {}
        except Exception:
            pass
        body = content[yaml_match.end():]
    return {"frontmatter": meta, "body": body, "path": path}

def write_page(
    title: str,
    body: str,
    tags: List[str],
    sources: List[str],
    related: List[str],
    page_type: str = "entities",
) -> Tuple[str, bool]:
    slug = slugify(title)
    existing = read_page(slug, page_type)
    today = date.today().isoformat()
    created = today

    if existing:
        fm = existing["frontmatter"]
        created = fm.get("created", today)
        existing_tags = set(fm.get("tags", []))
        existing_sources = set(fm.get("sources", []))
        existing_related = set(fm.get("related", []))
        tags = list(existing_tags | set(tags))
        sources = list(existing_sources | set(sources))
        related = list(existing_related | set(related))
        body = existing["body"].rstrip() + "\n\n" + body
        is_new = False
    else:
        is_new = True

    frontmatter = {
        "title": title,
        "tags": sorted(set(tags)),
        "created": created,
        "updated": today,
        "sources": sorted(set(sources)),
        "related": sorted(set(related)),
    }

    if existing and existing["frontmatter"].get("protected", False):
        frontmatter["protected"] = True

    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip()
    full_content = f"---\n{yaml_str}\n---\n\n{body}\n"

    path = _page_path(slug, page_type)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_content)
    logger.info(f"{'Created' if is_new else 'Updated'} wiki page: {path}")
    return slug, is_new

def delete_page(slug: str, page_type: str = "entities") -> bool:
    path = _page_path(slug, page_type)
    if os.path.isfile(path):
        os.remove(path)
        logger.info(f"Deleted wiki page: {path}")
        return True
    return False

def build_index() -> Dict[str, str]:
    index: Dict[str, str] = {}
    for subdir in SUBDIRS:
        dir_path = os.path.join(WIKI_DIR, subdir)
        if not os.path.isdir(dir_path):
            continue
        for fname in os.listdir(dir_path):
            if not fname.endswith(".md"):
                continue
            stem = fname[:-3]
            display = stem.replace("-", " ").replace("_", " ")
            index[stem.lower()] = display
            index[display.lower()] = display
    return index

def get_wiki_index() -> Dict[str, str]:
    if not hasattr(get_wiki_index, "_cache"):
        get_wiki_index._cache = build_index()
    return get_wiki_index._cache

def invalidate_index_cache():
    if hasattr(get_wiki_index, "_cache"):
        del get_wiki_index._cache

def lookup_entity(query: str) -> List[str]:
    index = get_wiki_index()
    lower_q = query.lower()
    words = set(re.findall(r"[a-zA-Z0-9-]+", lower_q))
    matches: List[Tuple[str, int]] = []
    for filename_lower, display_name in index.items():
        score = 0
        if filename_lower in lower_q or lower_q in filename_lower:
            score = len(filename_lower) * 2
        else:
            fname_words = set(re.findall(r"[a-z0-9-]+", filename_lower))
            common = words & fname_words
            if common:
                score = sum(len(w) for w in common)
        if score > 0:
            matches.append((display_name, score))
    matches.sort(key=lambda x: -x[1])
    return [name for name, _ in matches[:5]]

def append_to_index(slugs: List[Tuple[str, str, str]]):
    index_path = os.path.join(WIKI_DIR, "index.md")
    if not os.path.isfile(index_path):
        return
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    md = parse_frontmatter(content)
    body = md["body"]

    for slug, display_name, page_type in slugs:
        link = f"[[{display_name}]]"
        if link in body:
            continue
        section_header = "## Entities"
        if page_type == "concepts":
            section_header = "## Concepts (in wiki/concepts/)"
        elif page_type == "projects":
            section_header = "## Projects (in wiki/projects/)"

        entry = f"\n- {link}"
        section_pos = body.find(section_header)
        if section_pos != -1:
            next_section = body.find("\n## ", section_pos + len(section_header))
            if next_section != -1:
                body = body[:next_section] + entry + body[next_section:]
            else:
                body = body.rstrip() + entry + "\n"
        else:
            body = body.rstrip() + f"\n\n{section_header}\n\n{entry}\n"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(md["frontmatter_yaml"] + body)

def append_to_log(entry_text: str):
    log_path = os.path.join(WIKI_DIR, "log.md")
    if not os.path.isfile(log_path):
        return
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    md = parse_frontmatter(content)
    header = md["frontmatter_yaml"]
    body = md["body"]

    today = date.today().isoformat()
    log_entry = f"\n## [{today}] ingest | {entry_text}\n"
    body = body.rstrip() + log_entry + "\n"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(header + body)

def parse_frontmatter(content: str) -> Dict[str, Any]:
    yaml_match = re.match(r"^(---\s*\n.*?\n---)\s*\n", content, re.DOTALL)
    if yaml_match:
        return {
            "frontmatter_yaml": yaml_match.group(1) + "\n\n",
            "body": content[yaml_match.end():],
        }
    return {"frontmatter_yaml": "", "body": content}

def cross_reference_new_page(slug: str, display_name: str, page_type: str):
    for subdir in SUBDIRS:
        dir_path = os.path.join(WIKI_DIR, subdir)
        if not os.path.isdir(dir_path):
            continue
        for fname in os.listdir(dir_path):
            if not fname.endswith(".md"):
                continue
            fslug = fname[:-3]
            if fslug == slug:
                continue
            fpath = os.path.join(dir_path, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if slug.lower() in content.lower() or display_name.lower() in content.lower():
                page = read_page(fslug, subdir)
                if page:
                    existing_related = set(page["frontmatter"].get("related", []))
                    if display_name not in existing_related:
                        existing_related.add(display_name)
                        frontmatter = dict(page["frontmatter"])
                        frontmatter["related"] = sorted(existing_related)
                        frontmatter["updated"] = date.today().isoformat()
                        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip()
                        with open(fpath, "w", encoding="utf-8") as fw:
                            fw.write(f"---\n{yaml_str}\n---\n\n{page['body']}")
                        logger.info(f"Cross-referenced {display_name} in {fpath}")
