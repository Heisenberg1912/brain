"""Tests for the provider-agnostic LLM layer."""
import sys
from types import SimpleNamespace

import pytest

from brain.ai.adapters.openai import OpenAIAdapter
from brain.ai import llm as llm_layer
from brain.config import settings


def test_list_provider_profiles_marks_active_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_model", "gpt-test")

    profiles = llm_layer.list_provider_profiles()

    active = next(item for item in profiles if item["is_active"])
    assert active["key"] == "openai"
    assert active["model"] == "gpt-test"
    assert active["supports_json"] is True
    assert active["integration_style"] == "openai_compatible"
    assert active["open_source_ready"] is True
    assert any(item["key"] == "claude" for item in profiles)


def test_get_provider_profile_returns_claude_model(monkeypatch):
    monkeypatch.setattr(settings, "claude_model", "claude-test")

    profile = llm_layer.get_provider_profile("claude")

    assert profile["key"] == "claude"
    assert profile["model"] == "claude-test"


def test_register_provider_allows_plugging_custom_factory(monkeypatch):
    captured: dict[str, str | None] = {}

    def fake_factory(*, model=None):
        captured["model"] = model
        return SimpleNamespace(kind="fake-llm", model=model)

    profile = llm_layer.register_provider(
        "mock",
        label="Mock LLM",
        factory=fake_factory,
        model_resolver=lambda: "mock-default",
        positioning="Test-only pluggable provider.",
        supports_json=True,
        supports_system_instruction=True,
        open_source_ready=True,
    )

    monkeypatch.setattr(settings, "llm_provider", "mock")
    adapter = llm_layer.get_llm(model="mock-override")

    assert profile["key"] == "mock"
    assert adapter.kind == "fake-llm"
    assert captured["model"] == "mock-override"


def test_get_provider_profile_rejects_unknown_provider():
    with pytest.raises(ValueError):
        llm_layer.get_provider_profile("unknown-provider")


def test_openai_adapter_accepts_custom_base_url(monkeypatch):
    captured: dict[str, str] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setattr(settings, "openai_base_url", "http://localhost:8000/v1")
    monkeypatch.setattr(settings, "openai_api_key", "")

    adapter = OpenAIAdapter(model="local-llama")
    _ = adapter.client

    assert captured["base_url"] == "http://localhost:8000/v1"
    assert captured["api_key"] == "openai-compatible-local"
