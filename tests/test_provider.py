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


def test_plan_repairs_invalid_agent_operation_with_bounded_feedback(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    plan = demo_plan("CSAT", date(2026, 6, 30))
    bad = plan.model_dump(mode="json")
    bad["tasks"][0]["operation"] = "retrieve"
    replies = iter([json.dumps(bad), plan.model_dump_json()])
    monkeypatch.setattr(provider, "_chat", lambda *a, **kw: {"content": next(replies)})
    assert provider.plan("CSAT", date(2026, 6, 30)) == plan
    attempts = []

    def always_invalid(*a, **kw):
        attempts.append(1)
        return {"content": json.dumps(bad)}

    monkeypatch.setattr(provider, "_chat", always_invalid)
    with pytest.raises(ValueError, match="3 attempts"):
        provider.plan("CSAT", date(2026, 6, 30))
    assert len(attempts) == 3


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_http_status_diagnostic_and_safe_trace(monkeypatch, status):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    monkeypatch.setenv("MINISENSE_API_KEY", "unit-secret")
    provider = LLMProvider()
    response = httpx.Response(status, request=httpx.Request("POST", "http://localhost"),
                              text="unit-secret-private-response")
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **kw: response)
    with pytest.raises(RuntimeError, match=f"HTTP {status}"):
        provider._chat([{"role": "user", "content": "unit-secret"}])
    serialized = json.dumps(provider.exchanges)
    assert "unit-secret" not in serialized
    assert "private-response" not in serialized
    assert provider.exchanges[-1]["status"] == status


def test_transport_records_actual_tool_request_without_key(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    monkeypatch.setenv("MINISENSE_API_KEY", "unit-secret")
    provider = LLMProvider()
    message = {"tool_calls": [{"id": "call_1", "type": "function", "function": {
        "name": "compute_metrics", "arguments": '{"business_id":"b01"}'}}]}
    response = httpx.Response(200, request=httpx.Request("POST", "http://localhost"),
                              json={"choices": [{"message": message}], "usage": {"total_tokens": 10}})
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **kw: response)
    assert provider._chat([]) == message
    assert provider.exchanges[0]["response"] == message
    assert provider.exchanges[0]["request"]["model"] == "unit-test-model"
    assert "unit-secret" not in json.dumps(provider.exchanges)


def test_rate_limit_respects_bounded_retry_after(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    request = httpx.Request("POST", "http://localhost")
    responses = iter([
        httpx.Response(429, request=request, headers={"retry-after": "0"}),
        httpx.Response(200, request=request, json={"choices": [{"message": {"content": "{}"}}]}),
    ])
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **kw: next(responses))
    assert provider._chat([])["content"] == "{}"
    assert [call["status"] for call in provider.exchanges] == [429, 200]


def test_summary_repairs_omitted_evidence(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    replies = iter(['{"evidence_order":[0],"recommendation":null}',
                    '{"evidence_order":[0,1],"recommendation":"review"}'])
    monkeypatch.setattr(provider, "_chat", lambda *a, **kw: {"content": next(replies)})
    result = provider.select_evidence({"evidence": ["a", "b"], "allowed_recommendations": ["review"]})
    assert result.evidence_order == [0, 1]
    assert result.recommendation == "review"


def test_malformed_completion_message_fails_safely(monkeypatch):
    monkeypatch.setenv("MINISENSE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("MINISENSE_MODEL", "unit-test-model")
    provider = LLMProvider()
    response = httpx.Response(200, request=httpx.Request("POST", "http://localhost"),
                              json={"choices": [{"message": []}]})
    monkeypatch.setattr(httpx.Client, "post", lambda *a, **kw: response)
    with pytest.raises(RuntimeError, match="invalid completion envelope"):
        provider._chat([])
