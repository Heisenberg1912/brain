"""LLM adapter protocol — swap providers without changing service code."""
from __future__ import annotations

from typing import Any
from typing import Protocol


class LLMAdapter(Protocol):
    """Any LLM provider must implement this interface."""

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generate a text response given a prompt and optional system instruction."""
        ...

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict[str, Any] | list[Any]:
        """Generate a JSON response when the provider supports structured output."""
        ...
