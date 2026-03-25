"""Tests for the provider-agnostic LLM layer."""
from types import SimpleNamespace

import pytest

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
    )

    monkeypatch.setattr(settings, "llm_provider", "mock")
    adapter = llm_layer.get_llm(model="mock-override")

    assert profile["key"] == "mock"
    assert adapter.kind == "fake-llm"
    assert captured["model"] == "mock-override"


def test_get_provider_profile_rejects_unknown_provider():
    with pytest.raises(ValueError):
        llm_layer.get_provider_profile("unknown-provider")
