import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from src.llm_client import llm_client, parse_structured
from src.config import settings
from src.wiki.writer import build_index, lookup_entity, slugify

logger = logging.getLogger("chickensoup.agents.chat_ingest_agent")


class SuggestedPage(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    page_type: str = Field(default="entities", pattern=r"^(entities|concepts|projects)$")
    tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    summary: str = ""
    related: List[str] = Field(default_factory=list)
    body: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class TemporalReference(BaseModel):
    date: str = ""
    event: str = ""
    description: str = ""


class ChatIngestResult(BaseModel):
    suggested_pages: List[SuggestedPage] = Field(default_factory=list)
    user_name_detected: Optional[str] = None
    entities_discussed: List[str] = Field(default_factory=list)
    temporal_references: List[TemporalReference] = Field(default_factory=list)


class ChatIngestAgent:

    def _query_llm(self, prompt: str, system: str = "You are a precise conversation analyst.") -> Optional[str]:
        return llm_client.query_sync(
            prompt=prompt,
            system=system,
            priority="low",
            response_format="json_object",
            temperature=0.1,
        )

    async def analyze_conversation(
        self,
        messages: List[Dict[str, str]],
        conversation_id: str,
    ) -> Dict[str, Any]:
        existing_index = list(build_index().values())
        existing_str = "\n".join(f"- {name}" for name in sorted(existing_index)[:200])

        conversation_text = self._format_conversation(messages)
        user_entity = settings.CHAT_WIKI_USER_ENTITY_NAME

        prompt = f"""
You are analyzing a conversation between a user and an AI assistant about UFOs, aliens, and time travel for a knowledge wiki.

## Instructions

Extract NEW wiki-worthy content from this conversation. Focus on:
1. **Entities** — specific people, places, objects, events, programs
2. **Concepts** — theories, ideas, frameworks, claims
3. **Projects** — engineering work, experiments, architecture

Rules:
- Only extract pages for genuinely NEW material not already covered by existing wiki pages (listed below)
- Do NOT extract chit-chat, UI instructions, greetings, or system messages
- Set confidence based on how clearly the conversation supports each claim (0.9+ for explicit factual claims, 0.5 for speculation, 0.3 for vague mentions)
- Cross-reference at least 2-5 existing wiki pages via the `related` field
- Body must be full markdown with sections, 2-10 paragraphs

## User Name Detection

The current user entity in the wiki is "{user_entity}".
If the user has revealed their real name during this conversation, set `user_name_detected` to that name.
Otherwise set it to null.

## Temporal References

If the conversation mentions specific historical dates, events, or time periods, extract them as temporal_references.

## Current Wiki Pages (for deduplication and cross-referencing)
{existing_str}

## Conversation
{conversation_text}

Return ONLY a JSON object with this exact structure:
{{
    "suggested_pages": [
        {{
            "title": "Page title (natural name)",
            "page_type": "entities" or "concepts" or "projects",
            "tags": ["relevant", "tags"],
            "sources": ["conversation:{conversation_id}"],
            "summary": "1-2 sentence summary",
            "related": ["ExistingWikiPageName"],
            "body": "Full markdown body with ## sections and [[WikiLink]] cross-references",
            "confidence": 0.0-1.0
        }}
    ],
    "user_name_detected": null or "actual name",
    "entities_discussed": ["EntityName1", "EntityName2"],
    "temporal_references": [
        {{
            "date": "1947",
            "event": "Roswell incident",
            "description": "Mentioned in context of UFO crash recovery"
        }}
    ]
}}
"""

        llm_response = self._query_llm(prompt)
        if llm_response:
            result = parse_structured(llm_response, ChatIngestResult)
            if result:
                return self._normalize_result(result, conversation_id)

        return self._fallback_analysis(messages, conversation_id)

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}] {content}")
        return "\n\n".join(lines)

    def _normalize_result(
        self, data: ChatIngestResult, conversation_id: str
    ) -> Dict[str, Any]:
        pages = []
        for p in data.suggested_pages:
            page_type = p.page_type if p.page_type in ("entities", "concepts", "projects") else "entities"
            sources = list(p.sources)
            if f"conversation:{conversation_id}" not in sources:
                sources.append(f"conversation:{conversation_id}")

            pages.append({
                "title": p.title,
                "page_type": page_type,
                "tags": p.tags,
                "sources": sources,
                "summary": p.summary,
                "related": p.related,
                "body": p.body,
                "confidence": max(0.0, min(1.0, p.confidence)),
            })

        return {
            "suggested_pages": pages,
            "user_name_detected": data.user_name_detected or None,
            "entities_discussed": data.entities_discussed,
            "temporal_references": [t.model_dump() for t in data.temporal_references],
        }

    def _fallback_analysis(
        self, messages: List[Dict[str, str]], conversation_id: str
    ) -> Dict[str, Any]:
        topics = set()
        for msg in messages:
            content = msg.get("content", "")
            words = content.split()
            for i, w in enumerate(words):
                if w[0].isupper() and len(w) > 2 and i < len(words) - 1:
                    candidate = w.strip(".,!?;:")
                    if candidate and len(candidate) > 2:
                        topics.add(candidate)

        seen = build_index()
        novel_topics = [t for t in topics if t.lower() not in seen]

        pages = []
        for topic in novel_topics[:3]:
            matched = lookup_entity(topic)
            pages.append({
                "title": topic,
                "page_type": "entities",
                "tags": ["chat-extracted", "fallback"],
                "sources": [f"conversation:{conversation_id}"],
                "summary": f"Mentioned in conversation {conversation_id}.",
                "related": matched,
                "body": (
                    f"## Summary\n\n"
                    f"Mentioned in conversation `{conversation_id}` on "
                    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.\n\n"
                    f"## Context\n\n"
                    f"This topic was discussed in a conversation about UFOs, "
                    f"aliens, and time travel.\n\n"
                    f"## Claims\n\n"
                    f"- Mentioned in conversation, further investigation needed.\n"
                ),
                "confidence": 0.4,
            })

        return {
            "suggested_pages": pages,
            "user_name_detected": None,
            "entities_discussed": list(topics),
            "temporal_references": [],
        }
