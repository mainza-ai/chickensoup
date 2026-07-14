import json
import re
import time
import logging
import threading
import asyncio
import urllib.request
from typing import Optional, List, Dict, Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from src.config import settings
from src.discovery import get_active_model, get_active_base_url, get_active_provider
from src.llm_circuit_breaker import llm_circuit_breaker

logger = logging.getLogger("chickensoup.llm_client")

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    HIGH_PRIORITY = threading.Semaphore(settings.LLM_CLIENT_HIGH_PRIORITY_CONCURRENCY)
    LOW_PRIORITY = threading.Semaphore(settings.LLM_CLIENT_LOW_PRIORITY_CONCURRENCY)

    def __init__(self, default_timeout: float = None, default_max_tokens: int = None):
        self.default_timeout = default_timeout or settings.LLM_CLIENT_TIMEOUT
        self.default_max_tokens = default_max_tokens or settings.LLM_CLIENT_MAX_TOKENS
        self._metrics_enabled = False
        self._init_metrics()

    def _init_metrics(self):
        try:
            from src.observability import (
                llm_calls_total,
                llm_parse_failures_total,
                llm_semaphore_wait_seconds,
                llm_cache_hits_total,
            )
            self._llm_calls_total = llm_calls_total
            self._llm_parse_failures_total = llm_parse_failures_total
            self._llm_semaphore_wait_seconds = llm_semaphore_wait_seconds
            self._llm_cache_hits_total = llm_cache_hits_total
            self._metrics_enabled = True
        except Exception:
            pass

    def query_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        priority: str = "low",
        response_format: Optional[str] = None,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        if get_active_provider() == "simulated":
            return None

        sem = self.HIGH_PRIORITY if priority == "high" else self.LOW_PRIORITY
        timeout = timeout or self.default_timeout
        max_tokens = max_tokens or self.default_max_tokens
        model_name = model or get_active_model()
        url = f"{get_active_base_url()}/chat/completions"

        msgs = messages or []
        if not msgs:
            msgs = [
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        def _do_request() -> Optional[str]:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    return res_data["choices"][0]["message"]["content"]
            return None

        wait_start = time.monotonic()
        stage = response_format or "text"
        with sem:
            wait_elapsed = time.monotonic() - wait_start
            if self._metrics_enabled:
                try:
                    self._llm_semaphore_wait_seconds.record(wait_elapsed)
                except Exception:
                    pass
            try:
                result = llm_circuit_breaker.call(_do_request)
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "success"})
                    except Exception:
                        pass
                return result
            except RuntimeError as e:
                logger.warning(f"LLM circuit breaker open: {e}")
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "breaker_open"})
                    except Exception:
                        pass
                return None
            except Exception as e:
                logger.warning(f"LLM query failed: {e}")
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "error"})
                    except Exception:
                        pass
                return None

    async def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        priority: str = "low",
        response_format: Optional[str] = None,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.query_sync,
            prompt,
            system,
            priority,
            response_format,
            temperature,
            timeout,
            max_tokens,
            model,
            messages,
        )


llm_client = LLMClient()


def parse_structured(
    response: Optional[str],
    model: Type[T],
    field: str = None,
    logger: logging.Logger = None,
) -> Optional[T]:
    """Parse LLM response into a Pydantic model with multiple recovery strategies.

    Strategies:
      1. Direct json.loads + model validation
      2. Find JSON block in free text (```json or { } or [ ])
      3. Extract a specific top-level field from a JSON object (if field is set)
      4. Fallback — return None

    Returns the parsed model, or None if all strategies fail.
    """
    log = logger or logging.getLogger(__name__)

    if not response:
        return None

    # Strategy 1: Direct
    try:
        data = json.loads(response)
        if field:
            data = data[field]
        return model(**data)
    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        log.debug(f"parse_structured strategy 1 failed: {e}")

    # Strategy 2: Extract JSON from markdown or free text
    for pattern in [r"```json\n(.*?)\n```", r"```\n(.*?)\n```", r"\{.*\}"]:
        try:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                data = json.loads(match.group(1) if pattern != r"\{.*\}" else match.group(0))
                if field:
                    data = data[field]
                return model(**data)
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            log.debug(f"parse_structured strategy 2 ({pattern}) failed: {e}")

    # Strategy 3: If the response is a JSON array at top level
    try:
        data = json.loads(f'{{"{field}": {response}}}') if field else json.loads(response)
        if field:
            data = data[field]
        return model(**data)
    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        log.debug(f"parse_structured strategy 3 failed: {e}")

    log.warning(f"parse_structured: all strategies failed for model {model.__name__}")
    try:
        from src.observability import llm_parse_failures_total
        llm_parse_failures_total.add(1, {"model": model.__name__})
    except Exception:
        pass
    return None
