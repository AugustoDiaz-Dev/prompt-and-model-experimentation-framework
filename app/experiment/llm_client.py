import os
import logging
import httpx
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class LLMClient:
    async def generate_response(
        self, 
        prompt: str, 
        input_text: str, 
        model_name: str, 
        temperature: float, 
        max_tokens: int, 
        seed: Optional[int]
    ) -> Tuple[str, Dict[str, int]]:
        """
        Generates response using matching APIs or falls back to mock.
        Returns a tuple of (generated_text, token_usage).
        Token usage is a dict with 'prompt_tokens', 'completion_tokens', 'total_tokens'.
        """
        model_lower = model_name.lower()
        if "gpt" in model_lower:
            return await self._call_openai(prompt, input_text, model_name, temperature, max_tokens, seed)
        elif "claude" in model_lower:
            return await self._call_anthropic(prompt, input_text, model_name, temperature, max_tokens)
        else:
            return await self._mock_call(prompt, input_text, model_name)

    async def _call_openai(self, prompt: str, input_text: str, model_name: str, temperature: float, max_tokens: int, seed: Optional[int]) -> Tuple[str, Dict[str, int]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Falling back to mock response.")
            return await self._mock_call(prompt, input_text, model_name)

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text}
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                return content, usage
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return await self._mock_call(prompt, input_text, model_name)

    async def _call_anthropic(self, prompt: str, input_text: str, model_name: str, temperature: float, max_tokens: int) -> Tuple[str, Dict[str, int]]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Falling back to mock response.")
            return await self._mock_call(prompt, input_text, model_name)

        payload = {
            "model": model_name,
            "system": prompt,
            "messages": [
                {"role": "user", "content": input_text}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]
                usage_data = data.get("usage", {})
                usage = {
                    "prompt_tokens": usage_data.get("input_tokens", 0),
                    "completion_tokens": usage_data.get("output_tokens", 0),
                    "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
                }
                return content, usage
            except Exception as e:
                logger.error(f"Anthropic API error: {e}")
                return await self._mock_call(prompt, input_text, model_name)

    async def _mock_call(self, prompt: str, input_text: str, model_name: str) -> Tuple[str, Dict[str, int]]:
        import asyncio
        await asyncio.sleep(0.5)
        text_lower = input_text.lower()
        if "stock and a bond" in text_lower:
            content = "A stock is equity (ownership), while a bond is debt (a loan)."
        elif "compound interest" in text_lower:
            content = "Interest calculated on the initial principal and also on the accumulated interest of previous periods."
        elif "margin trading" in text_lower:
            content = "Margin trading amplifies both gains and losses. It carries the risk of a margin call if asset values drop."
        else:
            content = f"Mock logic based on {model_name} processing: '{input_text}'"
        
        prompt_t = len(prompt.split()) + len(input_text.split())
        comp_t = len(content.split())
        return content, {"prompt_tokens": prompt_t, "completion_tokens": comp_t, "total_tokens": prompt_t + comp_t}
