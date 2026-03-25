"""Anthropic Claude adapter."""
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


class ClaudeAdapter:
    """LLM adapter for Anthropic Claude."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.claude_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError("Install anthropic: pip install anthropic")
            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def _extract_text(self, response) -> str:
        blocks = getattr(response, "content", None) or []
        text_parts: list[str] = []
        for block in blocks:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(getattr(block, "text", "") or "")
        return "\n".join(part for part in text_parts if part).strip()

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        payload = {
            "model": self._model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload["system"] = system_instruction

        response = self.client.messages.create(**payload)
        return self._extract_text(response)

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict | list:
        text = self.generate(prompt, system_instruction=system_instruction)
        return json.loads(_extract_json_payload(text))
