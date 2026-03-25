"""Provider-agnostic LLM registry and factory."""
from __future__ import annotations

from typing import Any

from brain.ai.adapters import LLMAdapter
from brain.config import settings


def _openai_factory(*, model: str | None = None) -> LLMAdapter:
    from brain.ai.adapters.openai import OpenAIAdapter

    return OpenAIAdapter(model=model or settings.openai_model)


def _gemini_factory(*, model: str | None = None) -> LLMAdapter:
    from brain.ai.adapters.gemini import GeminiAdapter

    return GeminiAdapter(model=model or settings.gemini_model)


PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "openai": {
        "key": "openai",
        "label": "OpenAI",
        "positioning": "Strong general-purpose reasoning and structured generation.",
        "supports_text": True,
        "supports_json": True,
        "supports_system_instruction": True,
        "model_resolver": lambda: settings.openai_model,
        "factory": _openai_factory,
    },
    "gemini": {
        "key": "gemini",
        "label": "Gemini",
        "positioning": "Default low-friction provider for the current AI interface.",
        "supports_text": True,
        "supports_json": True,
        "supports_system_instruction": True,
        "model_resolver": lambda: settings.gemini_model,
        "factory": _gemini_factory,
    },
}


def register_provider(
    key: str,
    *,
    label: str,
    factory,
    model_resolver,
    positioning: str = "",
    supports_text: bool = True,
    supports_json: bool = False,
    supports_system_instruction: bool = False,
) -> dict[str, Any]:
    normalized = key.strip().lower()
    if not normalized:
        raise ValueError("Provider key is required")

    PROVIDER_REGISTRY[normalized] = {
        "key": normalized,
        "label": label,
        "positioning": positioning,
        "supports_text": supports_text,
        "supports_json": supports_json,
        "supports_system_instruction": supports_system_instruction,
        "model_resolver": model_resolver,
        "factory": factory,
    }
    return _build_provider_profile(normalized, is_active=False)


def _normalize_provider(provider: str | None = None) -> str:
    normalized = (provider or settings.llm_provider or "").strip().lower()
    if normalized not in PROVIDER_REGISTRY:
        supported = ", ".join(sorted(PROVIDER_REGISTRY))
        raise ValueError(f"Unsupported llm_provider: {provider or settings.llm_provider}. Supported providers: {supported}")
    return normalized


def _build_provider_profile(key: str, *, is_active: bool) -> dict[str, Any]:
    entry = PROVIDER_REGISTRY[key]
    model = entry["model_resolver"]()
    return {
        "key": entry["key"],
        "label": entry["label"],
        "model": model,
        "is_active": is_active,
        "supports_text": bool(entry.get("supports_text", True)),
        "supports_json": bool(entry.get("supports_json", False)),
        "supports_system_instruction": bool(entry.get("supports_system_instruction", False)),
        "positioning": entry.get("positioning", ""),
    }


def list_provider_profiles() -> list[dict[str, Any]]:
    active_provider = _normalize_provider()
    return [
        _build_provider_profile(key, is_active=(key == active_provider))
        for key in PROVIDER_REGISTRY
    ]


def get_provider_profile(provider: str | None = None) -> dict[str, Any]:
    key = _normalize_provider(provider)
    return _build_provider_profile(key, is_active=True)


def get_llm(provider: str | None = None, *, model: str | None = None) -> LLMAdapter:
    key = _normalize_provider(provider)
    entry = PROVIDER_REGISTRY[key]
    return entry["factory"](model=model)


def get_llm_profile() -> dict[str, Any]:
    active = get_provider_profile()
    return {
        "abstraction": "provider_registry",
        "active_provider": active["key"],
        "active_model": active["model"],
        "providers": list_provider_profiles(),
    }
