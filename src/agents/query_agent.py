import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.discovery import discover_active_provider
import urllib.request
import urllib.parse
import json

logger = logging.getLogger("chickensoup.agents.query_agent")

class ParsedQuery(BaseModel):
    intent: str = Field(..., description="Query intent: query, navigate, or status")
    entities: List[str] = Field(default_factory=list, description="Extracted entity names")
    structured_filters: Dict[str, Any] = Field(default_factory=dict, description="Extracted key-value filters (TQL-like)")
    confidence: float = Field(0.5, description="Confidence score of classification")

from src.cache import cache_decorator

class QueryAgent:
    """
    Parses and classifies user queries to identify intent, entities, and structured metadata.
    Supports a TQL-like structured syntax or performs LLM-based extraction.
    """
    
    def __init__(self):
        self.provider, self.base_url, self.models = discover_active_provider()
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
        if self.provider == "simulated":
            return None
        
        url = f"{self.base_url}/chat/completions"
        model_name = self.models[0] if self.models else "default-model"
        
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
            with urllib.request.urlopen(req, timeout=90.0) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    content = res_data["choices"][0]["message"]["content"]
                    return content
        except Exception as e:
            logger.warning(f"Failed to fetch classification from local LLM: {e}")
        return None

    def classify_and_parse(self, query: str) -> ParsedQuery:
        """
        Classifies query intent and extracts key attributes using a hybrid TQL parser and LLM extractor.
        """
        # 1. Classical TQL extraction fallback
        tql_parsed = self.parse_tql(query)
        if tql_parsed:
            logger.info("Successfully parsed query using TQL parser.")
            return tql_parsed

        # 2. LLM Ingest/Classification
        prompt = f"""
        Analyze the following user query and extract:
        1. intent: "query" (seeking info/lore), "navigate" (calculating/plotting a spacetime path/trajectory), or "status" (system health/status checks)
        2. entities: list of main subjects, people, places, projects mentioned
        3. structured_filters: key-value dictionary, e.g. {{"year": 1947, "confidence": 0.9}}
        4. confidence: float score between 0.0 and 1.0 representing how confident you are in this classification

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

        # 3. Basic Heuristic Fallback
        lower_q = query.lower()
        intent = "query"
        if "navigate" in lower_q or "trajectory" in lower_q or "path" in lower_q or "travel" in lower_q:
            intent = "navigate"
        elif "status" in lower_q or "health" in lower_q or "check" in lower_q:
            intent = "status"

        # Basic entity extraction (extract capitalized words or just use the query words)
        entities = []
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
