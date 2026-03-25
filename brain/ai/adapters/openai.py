"""OpenAI adapter."""
import json
import re

from brain.config import settings


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.+?)\s*```", stripped, re.DOTALL)
        if match:
            return match.group(1).strip()
    return stripped


class OpenAIAdapter:
    """LLM adapter for OpenAI (GPT-4, etc.)."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.openai_model
        self._base_url = (base_url or settings.openai_base_url or "").strip() or None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Install openai: pip install openai")
            client_kwargs = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
                if not client_kwargs["api_key"]:
                    client_kwargs["api_key"] = "openai-compatible-local"
            self._client = OpenAI(**client_kwargs)
        return self._client

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict | list:
        text = self.generate(prompt, system_instruction=system_instruction)
        return json.loads(_extract_json_payload(text))
