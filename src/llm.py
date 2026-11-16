"""Thin OpenAI-compatible chat client (Gemini / Ollama) with throttling and retries.

`chat()` returns (assistant message as a dict, usage dict). The assistant message is
passed back unchanged in later turns (keeps provider fields such as Gemini thought
signatures). Transient errors (429, 5xx, timeout) are retried with backoff; anything
else is raised and recorded by the caller as an error, never replaced by a fake answer.
"""
import time
from typing import Any


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, *, min_interval: float = 0.0,
                 temperature: float | None = None, max_retries: int = 4, timeout: float = 120.0) -> None:
        if not (base_url and api_key and model):
            raise ValueError("LLM_BASE_URL, LLM_API_KEY and LLM_MODEL must be set in .env")
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0)
        self.model, self.min_interval, self.temperature = model, min_interval, temperature
        self.max_retries = max_retries
        self._last = 0.0
        self.base_url = base_url

    def info(self) -> dict[str, Any]:
        return {"base_url": self.base_url, "model": self.model, "temperature": self.temperature,
                "min_interval_s": self.min_interval}

    def _throttle(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> tuple[dict, dict]:
        import openai
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto"}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                resp = self.client.chat.completions.create(**kwargs)
                break
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
                    openai.InternalServerError) as e:
                if attempt == self.max_retries:
                    raise
                delay = min(60, 5 * 2 ** attempt)
                print(f"  [llm] {type(e).__name__}, retry {attempt + 1}/{self.max_retries} in {delay}s")
                time.sleep(delay)
        msg = resp.choices[0].message.model_dump(exclude_none=True)
        msg["role"] = "assistant"
        u = resp.usage
        usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                 "completion_tokens": getattr(u, "completion_tokens", 0) or 0}
        return msg, usage