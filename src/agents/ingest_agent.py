import json
import logging
import urllib.request
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.discovery import get_active_model, get_active_base_url, get_active_provider
from src.wiki.writer import build_index, lookup_entity, slugify
from src.cache import cache_decorator

logger = logging.getLogger("chickensoup.agents.ingest_agent")

@dataclass
class SuggestedPage:
    title: str
    page_type: str
    tags: List[str]
    sources: List[str]
    summary: str
    related: List[str]
    body: str
    confidence: float

@dataclass
class IngestAnalysis:
    suggested_pages: List[SuggestedPage]
    confidence: float
    raw_text_preview: str

class IngestAgent:
    def __init__(self):
        pass

    def _query_llm(self, prompt: str, system: str = "You are a precise extraction engine.") -> Optional[str]:
        if get_active_provider() == "simulated":
            return None
        url = f"{get_active_base_url()}/chat/completions"
        model_name = get_active_model()
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30.0) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM query failed: {e}")
        return None

    def analyze_content(self, text: str, filename: Optional[str] = None) -> IngestAnalysis:
        existing_index = list(build_index().values())
        existing_str = "\n".join(f"- {name}" for name in sorted(existing_index)[:200])

        prompt = f"""
You are analyzing a document for a UFO/Aliens/Time Travel knowledge wiki.
Extract all meaningful entities, concepts, and projects mentioned.

Existing wiki pages (for cross-reference):
{existing_str}

Document (from file: {filename or 'unknown'}):
---
{text[:8000]}
---

Return ONLY a JSON object with this exact structure:
{{
    "suggested_pages": [
        {{
            "title": "Page title (natural name)",
            "page_type": "entities" or "concepts" or "projects",
            "tags": ["relevant", "tags"],
            "sources": ["{filename or 'uploaded-document'}"],
            "summary": "1-2 sentence summary of what this page is about",
            "related": ["existing wiki page names this should link to"],
            "body": "Full markdown body for the page. Include sections like ## Key Facts, ## Details, ## Claims. Use [[WikiLink]] syntax for cross-references.",
            "confidence": 0.0-1.0
        }}
    ],
    "confidence": 0.0-1.0
}}

Rules:
- Extract 1-5 pages. Don't create pages for things that already exist in the wiki index above — only for genuinely new entities/concepts/projects.
- For page_type: "entities" for specific people/places/objects/events, "concepts" for ideas/theories, "projects" for engineering work.
- Set confidence based on how clearly the document supports each page (0.9+ for explicit claims, 0.5 for vague mentions).
- Body should be in markdown with proper sections, 2-10 paragraphs.
- Always include "uploaded-document" (or the actual filename) in sources.
- Cross-reference at least 2-5 existing wiki pages via the related field and [[links]] in the body.
"""
        llm_response = self._query_llm(prompt)
        if llm_response:
            try:
                data = json.loads(llm_response)
                pages = []
                for p in data.get("suggested_pages", []):
                    pages.append(SuggestedPage(
                        title=p["title"],
                        page_type=p.get("page_type", "entities"),
                        tags=p.get("tags", []),
                        sources=p.get("sources", [filename or "uploaded-document"]),
                        summary=p.get("summary", ""),
                        related=p.get("related", []),
                        body=p.get("body", ""),
                        confidence=p.get("confidence", 0.5),
                    ))
                return IngestAnalysis(
                    suggested_pages=pages,
                    confidence=data.get("confidence", 0.5),
                    raw_text_preview=text[:500],
                )
            except Exception as e:
                logger.warning(f"Failed to parse LLM analysis: {e}")

        return self._fallback_analysis(text, filename)

    def _fallback_analysis(self, text: str, filename: Optional[str]) -> IngestAnalysis:
        lines = text.strip().split("\n")
        title = filename or "Uploaded Document"
        first_line = lines[0].strip().strip("#").strip() if lines else title
        page_title = first_line if len(first_line) < 80 else title
        body_lines = []
        body_lines.append(f"## Summary\n\nExtracted from {filename or 'uploaded document'}.\n")
        body_lines.append(text[:2000])
        body = "\n\n".join(body_lines)
        return IngestAnalysis(
            suggested_pages=[
                SuggestedPage(
                    title=page_title,
                    page_type="entities",
                    tags=["uploaded", "document"],
                    sources=[filename or "uploaded-document"],
                    summary=f"Auto-extracted from uploaded file: {filename or 'unknown'}",
                    related=lookup_entity(page_title),
                    body=body,
                    confidence=0.4,
                )
            ],
            confidence=0.4,
            raw_text_preview=text[:500],
        )

    def classify_page_type(self, title: str, summary: str, tags: List[str]) -> str:
        lower_title = title.lower()
        lower_summary = summary.lower()
        all_text = " ".join(t.lower() for t in tags) + " " + lower_title + " " + lower_summary
        if any(w in all_text for w in ["person", "people", "place", "location", "object", "craft", "event"]):
            return "entities"
        if any(w in all_text for w in ["project", "engineering", "architecture", "implementation"]):
            return "projects"
        return "concepts"

    def generate_wiki_pages(self, analysis: IngestAnalysis) -> List[Dict[str, Any]]:
        results = []
        for page in analysis.suggested_pages:
            page_type = page.page_type
            if page_type not in ("entities", "concepts", "projects"):
                page_type = self.classify_page_type(page.title, page.summary, page.tags)
            results.append({
                "title": page.title,
                "page_type": page_type,
                "tags": page.tags,
                "sources": page.sources,
                "summary": page.summary,
                "related": page.related,
                "body": page.body,
                "confidence": page.confidence,
            })
        return results
