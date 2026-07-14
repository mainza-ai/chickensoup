import logging
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from src.llm_client import llm_client, parse_structured
from src.wiki.writer import build_index, lookup_entity, slugify
from src.cache import cache_decorator

logger = logging.getLogger("chickensoup.agents.ingest_agent")


class SuggestedPage(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    page_type: str = Field(default="entities", pattern=r"^(entities|concepts|projects)$")
    tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    summary: str = ""
    related: List[str] = Field(default_factory=list)
    body: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class IngestResponse(BaseModel):
    """Shape of the LLM response for entity extraction."""
    suggested_pages: List[SuggestedPage] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class IngestAnalysis(BaseModel):
    suggested_pages: List[SuggestedPage] = Field(default_factory=list)
    confidence: float = 0.5
    raw_text_preview: str = ""

class IngestAgent:
    def __init__(self):
        pass

    def _query_llm(self, prompt: str, system: str = "You are a precise extraction engine.") -> Optional[str]:
        return llm_client.query_sync(
            prompt=prompt,
            system=system,
            priority="low",
            response_format="json_object",
            temperature=0.1,
        )

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
            result = parse_structured(llm_response, IngestResponse)
            if result:
                return IngestAnalysis(
                    suggested_pages=result.suggested_pages,
                    confidence=result.confidence,
                    raw_text_preview=text[:500],
                )

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
                    tags=["uploaded", "document", "fallback"],
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
        lower_tags = [t.lower() for t in tags]
        lower_title = title.lower()
        lower_summary = summary.lower()

        # Tag-based classification (most reliable)
        entity_tags = {"person", "people", "place", "location", "object", "craft",
                       "event", "whistleblower", "witness", "incident", "crash",
                       "sighting", "artifact", "device", "material"}
        if any(t in entity_tags for t in lower_tags):
            return "entities"

        project_tags = {"project", "program", "experiment", "mission", "operation"}
        if any(t in project_tags for t in lower_tags):
            return "projects"

        # Fallback to summary + title keyword matching (less reliable)
        # Only match whole words to avoid substring false positives
        all_text = " " + " ".join(lower_tags) + " " + lower_title + " " + lower_summary + " "
        entity_keywords = ["person", "people", "place", "location", "object", "craft", "event"]
        if any(f" {w} " in all_text for w in entity_keywords):
            return "entities"
        project_keywords = ["project", "engineering", "architecture", "implementation"]
        if any(f" {w} " in all_text for w in project_keywords):
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
