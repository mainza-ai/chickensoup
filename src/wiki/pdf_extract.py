import os
import shutil
import logging
from typing import Optional

from pypdf import PdfReader

from src.config import settings

logger = logging.getLogger("chickensoup.wiki.pdf_extract")


def _wiki_dir() -> str:
    """Resolve WIKI_DATA_DIR dynamically so monkeypatching settings works in tests."""
    wd = settings.WIKI_DATA_DIR
    if not os.path.isabs(wd):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        wd = os.path.join(project_root, wd)
    return wd


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pypdf.

    Returns the concatenated text of all pages joined by newlines.
    Returns an empty string if the PDF has no extractable text (e.g., scanned/image PDF).
    """
    try:
        reader = PdfReader(pdf_path)
        pages_text: list = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                pages_text.append(page_text)
        full_text = "\n\n".join(pages_text)
        if not full_text.strip():
            logger.warning("No extractable text from %s — may be a scanned/image PDF", pdf_path)
        return full_text
    except Exception as exc:
        logger.error("Failed to extract text from %s: %s", pdf_path, exc)
        return ""


def copy_pdf_to_raw(pdf_path: str, slug: str) -> Optional[str]:
    """Copy a PDF into wiki/raw/<slug>.pdf if not already present.

    Returns the relative path from project root (e.g., 'wiki/raw/<slug>.pdf')
    or None if the copy failed.
    """
    raw_dir = os.path.join(_wiki_dir(), "raw")
    os.makedirs(raw_dir, exist_ok=True)
    dest_path = os.path.join(raw_dir, f"{slug}.pdf")
    try:
        if not os.path.exists(dest_path):
            shutil.copy2(pdf_path, dest_path)
            logger.debug("Copied PDF to wiki/raw: %s -> %s", pdf_path, dest_path)
        rel = os.path.relpath(dest_path, os.path.dirname(_wiki_dir()))
        rel = rel.replace(os.sep, "/")
        return rel
    except Exception as exc:
        logger.error("Failed to copy PDF %s to wiki/raw: %s", pdf_path, exc)
        return None
