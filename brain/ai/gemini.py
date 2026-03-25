"""Google Gemini client wrapper — DEPRECATED, use adapters/gemini.py instead.

Kept for backward compatibility with CLI commands.
"""
from brain.ai.adapters.gemini import GeminiAdapter

_adapter = GeminiAdapter()


def generate(prompt: str, system_instruction: str | None = None) -> str:
    return _adapter.generate(prompt, system_instruction=system_instruction)
