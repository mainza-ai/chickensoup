import os
from pathlib import Path

from src.config import settings


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_project_root() -> Path:
    return _project_root()


def get_wiki_dir() -> Path:
    p = Path(settings.WIKI_DATA_DIR)
    if not p.is_absolute():
        p = _project_root() / p
    return p


def get_raw_dir() -> Path:
    return get_wiki_dir() / "raw"


def get_pulse_dir() -> Path:
    return get_raw_dir() / "pulse"


def get_almanac_dir() -> Path:
    return get_raw_dir() / "almanac"


def get_entities_dir() -> Path:
    return get_wiki_dir() / "entities"


def get_concepts_dir() -> Path:
    return get_wiki_dir() / "concepts"


def get_projects_dir() -> Path:
    return get_wiki_dir() / "projects"


def ensure_pulse_dir() -> Path:
    d = get_pulse_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_almanac_dir() -> Path:
    d = get_almanac_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d
