import json
import pytest
import httpx
from minisense.provider import LLMProvider
from minisense.agents import demo_plan
from datetime import date


def test_missing_provider_configuration(monkeypatch):
    monkeypatch.delenv("MINISENSE_BASE_URL", raising=False)
    monkeypatch.delenv("MINISENSE_MODEL", raising=False)
    with pytest.raises(ValueError, match="requires"):
        LLMProvider()


def test_transport_and_plan_contract(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    plan = demo_plan("CSAT in June 2026", date(2026, 6, 30))

    def mock_chat(messages, **kwargs):
        return {"content": plan.model_dump_json()}

    monkeypatch.setattr(provider, "_chat", mock_chat)
    assert provider.plan(plan.question, date(2026, 6, 30)) == plan
    with pytest.raises(ValueError):
        provider.plan("different question", date(2026, 6, 30))


def test_tool_contract(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    monkeypatch.setattr(provider, "_chat", lambda *a, **kw: {"tool_calls": []})
    task = demo_plan("CSAT", date(2026, 6, 30)).tasks[0]
    with pytest.raises(ValueError, match="exactly one"):
        provider.call_tool(task, {})


def test_http_failure_does_not_leak_secrets(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()

    def fail(*a, **kw):
        raise httpx.ConnectError("private-secret-value")

    monkeypatch.setattr(httpx.Client, "post", fail)
    with pytest.raises(RuntimeError) as exc:
        provider._chat([])
    assert "private-secret-value" not in str(exc.value)
