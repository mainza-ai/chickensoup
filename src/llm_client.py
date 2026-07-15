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
from src.discovery import get_active_model, get_active_base_url, get_active_provider, get_cloud_api_key
from src.llm_circuit_breaker import llm_circuit_breaker
from src.progress_tracker import increment as progress_inc, update as progress_update

logger = logging.getLogger("chickensoup.llm_client")

T = TypeVar("T", bound=BaseModel)

_CLOUD_PROVIDERS = frozenset({"nvidia", "openrouter", "custom"})


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

    def _effective_timeout(self, timeout: Optional[float] = None) -> float:
        if timeout is not None:
            return timeout
        provider = get_active_provider()
        if provider in _CLOUD_PROVIDERS:
            return settings.LLM_CLIENT_CLOUD_TIMEOUT
        return settings.LLM_CLIENT_LOCAL_TIMEOUT

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
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if get_active_provider() == "simulated":
            return None

        sem = self.HIGH_PRIORITY if priority == "high" else self.LOW_PRIORITY
        timeout = self._effective_timeout(timeout)
        max_tokens = max_tokens or self.default_max_tokens
        model_name = model or get_active_model()
        url = f"{get_active_base_url()}/chat/completions"
        provider = get_active_provider()

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
            "top_p": 0.95,
        }
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
        if extra_body:
            payload.update(extra_body)

        def _build_headers() -> Dict[str, str]:
            headers = {"Content-Type": "application/json"}
            if provider in _CLOUD_PROVIDERS:
                api_key = get_cloud_api_key(provider)
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            return headers

        def _do_request(override_model: str = None, request_timeout: Optional[float] = None) -> Optional[str]:
            current_model = override_model or model_name
            payload["model"] = current_model
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=_build_headers(),
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=request_timeout or timeout) as response:
                    if response.status == 200:
                        res_data = json.loads(response.read().decode("utf-8"))
                        return res_data["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                if e.code == 503:
                    raise
                logger.warning(f"LLM HTTP {e.code} on model {current_model}: {e}")
                return None
            return None

        def _try_models() -> Optional[str]:
            models_to_try = [model_name]

            for attempt, m in enumerate(models_to_try):
                try:
                    model_timeout = min(timeout, 15.0) if attempt > 0 else timeout
                    result = llm_circuit_breaker.call(lambda m=m, t=model_timeout: _do_request(override_model=m, request_timeout=t))
                    if result:
                        return result
                    if attempt < len(models_to_try) - 1:
                        logger.info(f"LLM model {m} returned empty, trying fallback model {models_to_try[attempt+1]}")
                except RuntimeError:
                    raise
                except urllib.error.HTTPError as e:
                    if e.code in (503, 429) and attempt < len(models_to_try) - 1:
                        logger.warning(f"LLM model {m} returned {e.code}, trying fallback model {models_to_try[attempt+1]}")
                        continue
                    return None
                except Exception as e:
                    if attempt < len(models_to_try) - 1:
                        logger.warning(f"LLM model {m} failed: {e}, trying fallback model {models_to_try[attempt+1]}")
                        continue
                    return None
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
                result = _try_models()
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "success"})
                    except Exception:
                        pass
                progress_inc("llm_client", "total_calls")
                progress_inc("llm_client", "success_calls")
                progress_update("llm_client", breaker_open="false")
                return result
            except RuntimeError as e:
                logger.warning(f"LLM circuit breaker open: {e}")
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "breaker_open"})
                    except Exception:
                        pass
                progress_inc("llm_client", "total_calls")
                progress_inc("llm_client", "failed_calls")
                progress_update("llm_client", breaker_open="true")
                return None
            except Exception as e:
                logger.warning(f"LLM query failed: {e}")
                if self._metrics_enabled:
                    try:
                        self._llm_calls_total.add(1, {"stage": stage, "status": "error"})
                    except Exception:
                        pass
                progress_inc("llm_client", "total_calls")
                progress_inc("llm_client", "failed_calls")
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
        extra_body: Optional[Dict[str, Any]] = None,
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
            extra_body,
        )


llm_client = LLMClient()


def parse_structured(
    response: Optional[str],
    model: Type[T],
    field: str = None,
    logger: logging.Logger = None,
) -> Optional[T]:
    log = logger or logging.getLogger(__name__)

    if not response:
        return None

    # Strategy 1: Direct
    try:
        data = json.loads(response)
        if field:
            if isinstance(data, dict):
                data = data[field]
            elif isinstance(data, list) and field:
                return model(**{field: data})
        return model(**data)
    except (json.JSONDecodeError, ValidationError, KeyError, TypeError, IndexError) as e:
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

    # Strategy 3: Find first { and parse from there (handles explanatory text before JSON)
    try:
        start = response.index("{")
        end = response.rindex("}")
        chunk = response[start:end+1]
        data = json.loads(chunk)
        if field:
            if isinstance(data, dict):
                data = data[field]
            elif isinstance(data, list) and field:
                return model(**{field: data})
        return model(**data)
    except (ValueError, json.JSONDecodeError, ValidationError, KeyError, TypeError) as e:
        log.debug(f"parse_structured strategy 3 failed: {e}")

    # Strategy 4: Handle LLM returning a list at top level — wrap in expected field
    try:
        parsed = json.loads(response)
        if isinstance(parsed, list) and field:
            return model(**{field: parsed})
        return model(**parsed)
    except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as e:
        log.debug(f"parse_structured strategy 4 failed: {e}")

    log.debug(f"parse_structured: all strategies failed for model {model.__name__}")
    log.debug(f"Raw response (first 500 chars): {response[:500]}")
    try:
        from src.observability import llm_parse_failures_total
        llm_parse_failures_total.add(1, {"model": model.__name__})
    except Exception:
        pass
    return None
