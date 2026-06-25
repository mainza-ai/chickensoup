import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from src.discovery import get_active_model, get_active_base_url, get_active_provider
from src.config import settings
from src.wiki.writer import build_index, lookup_entity, slugify

logger = logging.getLogger("chickensoup.agents.chat_ingest_agent")


class ChatIngestAgent:

    def _query_llm(self, prompt: str, system: str = "You are a precise conversation analyst.") -> Optional[str]:
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
            "response_format": {"type": "json_object"},
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Chat ingest LLM query failed: {e}")
        return None

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
            try:
                data = json.loads(llm_response)
                return self._normalize_result(data, conversation_id)
            except Exception as e:
                logger.warning(f"Failed to parse chat ingest LLM response: {e}")

        return self._fallback_analysis(messages, conversation_id)

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}] {content}")
        return "\n\n".join(lines)

    def _normalize_result(
        self, data: dict, conversation_id: str
    ) -> Dict[str, Any]:
        pages = []
        for p in data.get("suggested_pages", []):
            page_type = p.get("page_type", "entities")
            if page_type not in ("entities", "concepts", "projects"):
                page_type = "entities"

            sources = p.get("sources", [f"conversation:{conversation_id}"])
            if f"conversation:{conversation_id}" not in sources:
                sources.append(f"conversation:{conversation_id}")

            pages.append({
                "title": p["title"],
                "page_type": page_type,
                "tags": p.get("tags", []),
                "sources": sources,
                "summary": p.get("summary", ""),
                "related": p.get("related", []),
                "body": p.get("body", ""),
                "confidence": max(0.0, min(1.0, p.get("confidence", 0.5))),
            })

        return {
            "suggested_pages": pages,
            "user_name_detected": data.get("user_name_detected") or None,
            "entities_discussed": data.get("entities_discussed", []),
            "temporal_references": data.get("temporal_references", []),
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
