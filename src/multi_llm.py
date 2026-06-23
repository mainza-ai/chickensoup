import logging
import asyncio
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple
from src.discovery import discover_active_provider
from src.cache import cache_decorator

logger = logging.getLogger("chickensoup.multi_llm")

class MultiLLMConsensus:
    """
    Orchestrates consensus matching and result collation across multiple active LLM provider models.
    """
    def __init__(self):
        self.provider, self.base_url, self.models = discover_active_provider()

    async def generate_consensus(self, prompt: str, system_instruction: str = "You are an expert consensus analyzer.") -> Dict[str, Any]:
        """
        Queries all discovered models for the prompt, computes agreement consensus scores,
        and collates the final consensus response.
        """
        # If simulated, return standard mocked consensus output
        if self.provider == "simulated" or not self.models:
            return self._generate_mocked_consensus(prompt)

        # We will query up to 3 models from the active provider to keep it fast
        models_to_query = self.models[:3]
        tasks = [self._query_model_async(model, prompt, system_instruction) for model in models_to_query]
        responses = await asyncio.gather(*tasks)

        valid_responses = [resp for resp in responses if resp is not None]
        if not valid_responses:
            return self._generate_mocked_consensus(prompt)

        # Collate responses and calculate consensus
        consensus_data = self._calculate_consensus(valid_responses)
        return consensus_data

    async def _query_model_async(self, model: str, prompt: str, system_instruction: str) -> Tuple[str, str]:
        """
        Helper method to run urllib request in an executor since it is blocking.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._query_model_sync, model, prompt, system_instruction)

    def _query_model_sync(self, model: str, prompt: str, system_instruction: str) -> Tuple[str, str]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
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
                    data = json.loads(response.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    return model, content
        except Exception as e:
            logger.warning(f"Error querying model {model} on {self.provider}: {e}")
        return model, ""

    def _calculate_consensus(self, responses: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Calculates simple agreement/consensus metrics between responses.
        For production, we evaluate semantic similarity or keyword overlap.
        """
        non_empty = [resp for resp in responses if resp[1].strip()]
        if not non_empty:
            return {
                "consensus_response": "No valid model responses retrieved.",
                "agreement_score": 0.0,
                "individual_responses": {}
            }

        # Select the response from the first model as the anchor
        anchor_model, anchor_text = non_empty[0]
        
        # Calculate keyword overlap similarity as a simple proxy for agreement
        words_anchor = set(anchor_text.lower().split())
        agreements = []
        for model, text in non_empty:
            words_other = set(text.lower().split())
            intersection = words_anchor.intersection(words_other)
            union = words_anchor.union(words_other)
            jaccard = len(intersection) / len(union) if union else 1.0
            agreements.append(jaccard)

        agreement_score = sum(agreements) / len(agreements) if agreements else 1.0

        return {
            "consensus_response": anchor_text,
            "agreement_score": round(agreement_score, 3),
            "individual_responses": {model: text for model, text in non_empty}
        }

    def _generate_mocked_consensus(self, prompt: str) -> Dict[str, Any]:
        simulated_res = {
            "consensus_response": f"Consensus matching: Resolved prompt - {prompt}",
            "agreement_score": 0.95,
            "individual_responses": {
                "mock-gpt-4": f"Consensus response from mock-gpt-4 for: {prompt}",
                "mock-llama-3": f"Consensus response from mock-llama-3 for: {prompt}"
            }
        }
        return simulated_res
