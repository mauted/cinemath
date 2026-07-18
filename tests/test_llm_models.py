"""Unit tests for LLM model selection."""

from __future__ import annotations

import cinemath.llm as llm_mod


def test_classify_model_defaults_to_haiku(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_CLASSIFY_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert llm_mod._classify_model() == llm_mod.DEFAULT_CLASSIFY_MODEL


def test_teach_model_defaults_to_sonnet(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_TEACH_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert llm_mod._teach_model() == llm_mod.DEFAULT_TEACH_MODEL


def test_specific_model_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_CLASSIFY_MODEL", "cheap")
    monkeypatch.setenv("ANTHROPIC_TEACH_MODEL", "smart")
    assert llm_mod._classify_model() == "cheap"
    assert llm_mod._teach_model() == "smart"
