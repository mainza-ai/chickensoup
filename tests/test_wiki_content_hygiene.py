"""Lint: ensure no internal/development markers appear in public wiki dirs.

Public wiki dirs: wiki/entities/, wiki/concepts/, wiki/projects/
Internal wiki dir: wiki/dev/

If any internal marker appears in a public dir, CI fails.
"""
import re
import sys
from pathlib import Path

PUBLIC_DIRS = [
    Path("wiki/entities"),
    Path("wiki/concepts"),
    Path("wiki/projects"),
]

DEV_DIR = Path("wiki/dev")

# Patterns that are unambiguous markers of internal/developer content.
# Uses whole-word / anchored matching to avoid false positives on common
# words (e.g. "secret" in "secret program", "token" in physics context).
INTERNAL_PATTERNS = [
    # Specific backend module files (not generic "src/")
    re.compile(r"src/(?:agents|knowledge_graph|wiki|scheduler|discovery|resource_ledger|staleness_queue|idle_sentinel|almanac|quantum_credibility|pulse_writer|last30days_adapter|field_manipulator|cuda_simulation|pdf_extract|api)/(?:auth|backup|cleanup|ingest|watcher|writer|path|models|main|config|pulse_agent|chat_ingest_agent|research_agent|query_agent|navigation_agent)\.py"),
    # Python logger namespaced under chickensoup
    re.compile(r"chickensoup\.(?:wiki|wiki\.backup|wiki\.cleanup|wiki\.ingest|observability|api|auth|agents|knowledge_graph|scheduler|discovery|almanac|pulse_writer|last30days)"),
    # Specific env var names (system config, not generic words)
    re.compile(r"(?i)\b(?:WIKI_BACKUP_DIR|WIKI_BACKUP_ENABLED|WIKI_BACKUP_RETENTION|WIKI_DATA_DIR|WIKI_MIN_CONFIDENCE|WIKI_AUTO_CREATE|CHAT_WIKI_USER_ENTITY_NAME|LAST30DAYS_ENABLED|MONTHLY_BUDGET_USD|COST_PER_PULL_USD|LAST30DAYS_DEDUP_WINDOW|PULSE_TIMEOUT|MAX_CLAIMS|SOCIAL_TRACTION_WEIGHT|DIVERGENCE_SPIKE_THRESHOLD|ALMANAC_INTERVAL|API_KEY|LOG_IGNORE_PATTERNS|WIKI_BACKUP_RETENTION_DAYS)\b"),
    # Install commands for developer skills
    re.compile(r"npx\s+skills\s+add"),
    # Internal binary references
    re.compile(r"npx\s+last30days"),
    # Absolute user paths (macOS / Linux home)
    re.compile(r"(?:/Users/|/home/|/var/folders/)\S+"),
]


def test_no_internal_markers_in_public_wiki():
    failures = []
    for public_dir in PUBLIC_DIRS:
        if not public_dir.is_dir():
            continue
        for md_file in sorted(public_dir.rglob("*.md")):
            # index.md and log.md are exempt — they get separate treatment
            if md_file.name in {"index.md", "log.md"}:
                continue
            content = md_file.read_text(encoding="utf-8")
            for pattern in INTERNAL_PATTERNS:
                match = pattern.search(content)
                if match:
                    failures.append(
                        f"{md_file}: {match.group(0)!r}"
                    )

    if failures:
        print("FAIL: internal content markers found in public wiki dirs:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)


def test_dev_dir_exists():
    assert DEV_DIR.is_dir(), f"Expected wiki/dev/ directory to exist, got: {DEV_DIR}"


if __name__ == "__main__":
    test_dev_dir_exists()
    test_no_internal_markers_in_public_wiki()
    print("OK: wiki content hygiene checks passed")
