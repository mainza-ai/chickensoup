import json
import logging
import threading
import asyncio
import urllib.request
from typing import Optional, List, Dict, Any

from src.config import settings
from src.discovery import get_active_model, get_active_base_url, get_active_provider
from src.llm_circuit_breaker import llm_circuit_breaker

logger = logging.getLogger("chickensoup.llm_client")


class LLMClient:
    HIGH_PRIORITY = threading.Semaphore(settings.LLM_CLIENT_HIGH_PRIORITY_CONCURRENCY)
    LOW_PRIORITY = threading.Semaphore(settings.LLM_CLIENT_LOW_PRIORITY_CONCURRENCY)

    def __init__(self, default_timeout: float = None, default_max_tokens: int = None):
        self.default_timeout = default_timeout or settings.LLM_CLIENT_TIMEOUT
        self.default_max_tokens = default_max_tokens or settings.LLM_CLIENT_MAX_TOKENS

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

        with sem:
            try:
                return llm_circuit_breaker.call(_do_request)
            except RuntimeError as e:
                logger.warning(f"LLM circuit breaker open: {e}")
                return None
            except Exception as e:
                logger.warning(f"LLM query failed: {e}")
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
