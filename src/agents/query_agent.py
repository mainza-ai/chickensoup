import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from src.discovery import get_discovered, get_active_model, get_active_base_url, get_active_provider
import urllib.request
import urllib.parse
import json

logger = logging.getLogger("chickensoup.agents.query_agent")

WIKI_ENTITY_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki", "entities"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki", "concepts"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "wiki", "projects"),
]

class ParsedQuery(BaseModel):
    intent: str = Field(..., description="Query intent: query, navigate, or status")
    entities: List[str] = Field(default_factory=list, description="Extracted entity names")
    structured_filters: Dict[str, Any] = Field(default_factory=dict, description="Extracted key-value filters (TQL-like)")
    confidence: float = Field(0.5, description="Confidence score of classification")

from src.cache import cache_decorator

def _build_wiki_index() -> Dict[str, str]:
    """Build a mapping of lowercase-filename → display name from wiki directories."""
    index: Dict[str, str] = {}
    for d in WIKI_ENTITY_DIRS:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".md"):
                continue
            stem = fname[:-3]
            display = stem.replace("-", " ").replace("_", " ")
            index[stem.lower()] = display
            index[display.lower()] = display
    return index


def _get_wiki_index() -> Dict[str, str]:
    if not hasattr(_get_wiki_index, "_cache"):
        _get_wiki_index._cache = _build_wiki_index()
    return _get_wiki_index._cache


def invalidate_wiki_index():
    if hasattr(_get_wiki_index, "_cache"):
        del _get_wiki_index._cache


def get_wiki_index() -> Dict[str, str]:
    return _get_wiki_index()


def _wiki_entity_lookup(query: str) -> List[str]:
    """
    Fuzzy-match query words against wiki filenames.
    Returns display names of matching wiki pages (sorted by relevance).
    """
    index = _get_wiki_index()
    lower_q = query.lower()
    words = set(re.findall(r"[a-zA-Z0-9-]+", lower_q))

    matches: List[Tuple[str, int]] = []
    for filename_lower, display_name in index.items():
        score = 0
        if filename_lower in lower_q or lower_q in filename_lower:
            score = len(filename_lower) * 2
        else:
            filename_words = set(re.findall(r"[a-z0-9-]+", filename_lower))
            common = words & filename_words
            if common:
                score = sum(len(w) for w in common)
        if score > 0:
            matches.append((display_name, score))

    matches.sort(key=lambda x: -x[1])
    return [name for name, _ in matches[:5]]


class QueryAgent:
    """
    Parses and classifies user queries to identify intent, entities, and structured metadata.
    Supports a TQL-like structured syntax or performs LLM-based extraction.
    """
    
    def __init__(self):
        self.provider, self.base_url, self.models = get_discovered(depth="fresh")
        logger.info(f"QueryAgent initialized with provider: {self.provider} ({self.base_url})")

    def parse_tql(self, query: str) -> Optional[ParsedQuery]:
        """
        Attempts to parse structured Temporal Query Language (TQL) syntax:
        e.g., 'Roswell incident TYPE:Event YEAR:1947 CONFIDENCE:0.9'
        """
        # Quick regex check for key:value patterns
        matches = re.findall(r"(\w+):([\w\d.-]+)", query)
        if not matches:
            return None
            
        filters = {}
        for key, val in matches:
            # Clean up key/value
            k = key.lower()
            if val.replace(".", "").isdigit():
                v = float(val) if "." in val else int(val)
            else:
                v = val
            filters[k] = v
            
        # Clean query string to extract entities (remove the key:val parts)
        cleaned = re.sub(r"\w+:[\w\d.-]+", "", query).strip()
        entities = [cleaned] if cleaned else []
        
        # Simple intent heuristic
        intent = "query"
        if "navigate" in query.lower() or "origin" in filters or "destination" in filters or "year" in filters:
            intent = "navigate"
        elif "status" in query.lower() or "health" in query.lower():
            intent = "status"

        return ParsedQuery(
            intent=intent,
            entities=entities,
            structured_filters=filters,
            confidence=0.95
        )

    @cache_decorator(prefix="llm", ttl=300)
    def _query_local_llm(self, prompt: str) -> Optional[str]:
        if get_active_provider() == "simulated":
            return None
        
        url = f"{get_active_base_url()}/chat/completions"
        model_name = get_active_model()
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a precise classifier. Return ONLY valid JSON and nothing else."},
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
            with urllib.request.urlopen(req, timeout=15.0) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    content = res_data["choices"][0]["message"]["content"]
                    return content
        except Exception as e:
            logger.warning(f"Failed to fetch classification from local LLM: {e}")
        return None

    def classify_and_parse(self, query: str) -> ParsedQuery:
        """
        Classifies query intent and extracts key attributes using a hybrid TQL parser,
        wiki file matching, and LLM extractor.
        """
        # 0. Wiki file entity lookup — done first so both LLM and fallback benefit
        wiki_matches = _wiki_entity_lookup(query)
        if wiki_matches:
            logger.info(f"Wiki entity matches from query: {wiki_matches}")

        # 1. Classical TQL extraction fallback
        tql_parsed = self.parse_tql(query)
        if tql_parsed:
            logger.info("Successfully parsed query using TQL parser.")
            return tql_parsed

        # 2. LLM Ingest/Classification with discovered wiki entities as context
        wiki_hint = ""
        if wiki_matches:
            wiki_hint = f"\nKnown wiki pages matching this query: {', '.join(wiki_matches)}\nUse these as primary entities when relevant."

        prompt = f"""
        Analyze the following user query and extract intent, entities, and structured filters.{wiki_hint}

        Intent definitions:
        - "query": User seeks information, lore, answers, explanations, or wants to visualize/plot data about a topic. Use "query" when the user asks about something specific (people, places, events, concepts) — even if they use words like "plot", "map", or "chart".
        - "navigate": User wants to calculate a spacetime trajectory, travel through time, or plot a course from one specific point to another (e.g., "navigate to 1947", "travel to Roswell"). This typically involves explicit origin/destination or year targets.
        - "status": User wants system health, component status, or operational checks.

        Examples:
        - "Plot timelines connected to Element 115" → intent: "query" (info about Element 115)
        - "What happened in Roswell in 1947?" → intent: "query"
        - "Navigate from Earth-2026 to Earth-1947" → intent: "navigate"
        - "Navigate to 1947" → intent: "navigate"
        - "Show system status" → intent: "status"

        User query: "{query}"

        Return ONLY a JSON object:
        {{
            "intent": "query" | "navigate" | "status",
            "entities": ["entity1", ...],
            "structured_filters": {{...}},
            "confidence": 0.85
        }}
        """
        llm_response = self._query_local_llm(prompt)
        if llm_response:
            try:
                data = json.loads(llm_response)
                return ParsedQuery(**data)
            except Exception as e:
                logger.warning(f"Error parsing LLM response: {e}. Falling back to default parser.")

        # 3. Heuristic Fallback with wiki-aware entity extraction
        lower_q = query.lower()
        intent = "query"
        if "navigate" in lower_q or "trajectory" in lower_q or "path" in lower_q or "travel" in lower_q:
            intent = "navigate"
        elif "status" in lower_q or "health" in lower_q or "check" in lower_q:
            intent = "status"

        # Entity extraction: prefer wiki matches, fall back to capitalized words, fall back to query
        entities = []
        if wiki_matches:
            entities = wiki_matches
        else:
            words = query.split()
            capitalized = [w.strip("?,.!") for w in words if w and w[0].isupper()]
            if capitalized:
                entities = capitalized
            else:
                entities = [query]

        return ParsedQuery(
            intent=intent,
            entities=entities,
            structured_filters={},
            confidence=0.5
        )
