from minisense.cli import evaluate
from minisense.agents import Orchestrator
from minisense.analytics import SurveyStore
from minisense.dataset import generate
from minisense.contracts import Retrieval, Chunk
import json
import pytest


class FixtureIndex:
    def retrieve(self, query, **kwargs):
        result = Retrieval(
            query=query,
            chunks=[
                Chunk(
                    id="faq-01",
                    source="faq.txt",
                    content="Q: What is your average wait time?\nA: Under ten minutes.",
                ),
                Chunk(
                    id="faq-02",
                    source="faq.txt",
                    content="Q: What is your CSAT target?\nA: 4.5+. Below 4.0 triggers a review.",
                ),
                Chunk(
                    id="faq-03", source="faq.txt",
                    content="Q: How do you handle complaints?\nA: Escalate to the shift manager.",
                ),
            ],
        )
        relevant = "CSAT" if "CSAT" in query else "complaints" if "complaint" in query else "wait time"
        result.chunks.sort(key=lambda c: relevant not in c.content)
        return result


def test_evaluation_scopes_and_comparisons(tmp_path):
    output = tmp_path / "evaluation.json"
    assert (
        evaluate(Orchestrator(SurveyStore(generate(100)), FixtureIndex()), output)[
            "questions"
        ]
        == 3
    )
    rows = json.loads(output.read_text())["results"]
    assert rows[1]["correctness_checks"]["comparison_rate_delta"]
    assert rows[2]["correctness_checks"]["target_trigger"]


def test_evaluation_rejects_wrong_scope(tmp_path):
    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    original = app.ask

    def wrong(question):
        out = original(question)
        for task in out.plan.tasks:
            if task.agent == "data":
                task.business_id = "b99"
        return out

    app.ask = wrong
    with pytest.raises(ValueError, match="failed checks"):
        evaluate(app, tmp_path / "out.json")


def test_evaluation_accepts_equivalent_task_order(tmp_path):
    from minisense.agents import demo_plan

    class ReorderedProvider:
        def plan(self, question, latest):
            plan = demo_plan(question, latest)
            plan.tasks.reverse()
            return plan

    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    # Exercise the real scheduler, analytics and summary; only planning is a fixture.
    app.provider = ReorderedProvider()
    assert evaluate(app, tmp_path / "evaluation.json")["questions"] == 3


def test_evaluation_missing_data_is_failed_check(tmp_path):
    from minisense.contracts import Plan, Task

    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    original = app.ask

    def missing(question):
        out = original(question)
        out.plan = Plan(question=question, tasks=[
            Task(id="summary", agent="summary", operation="synthesize")
        ])
        out.agents_invoked = ["summary"]
        out.results = {}
        return out

    app.ask = missing
    output = tmp_path / "evaluation.json"
    with pytest.raises(ValueError, match="failed checks"):
        evaluate(app, output)
    assert len(json.loads(output.read_text())["results"]) == 3


def test_evaluation_preserves_partial_failures(tmp_path):
    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    original = app.ask

    def fail_second(question):
        if "May to June" in question:
            raise RuntimeError("private-secret-provider-body")
        return original(question)

    app.ask = fail_second
    output = tmp_path / "evaluation.json"
    with pytest.raises(ValueError, match="failed checks"):
        evaluate(app, output)
    saved = output.read_text()
    rows = json.loads(saved)["results"]
    assert len(rows) == 3
    assert rows[1]["status"] == "failed"
    assert "private-secret" not in saved
    assert rows[2]["correctness_checks"]["target_trigger"]


def test_failure_trace_is_snapshot_not_shared_provider_buffer(tmp_path):
    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    shared = []

    def fail(question):
        shared.clear()
        shared.append({"question": question})
        app.last_trace = {"model_calls": shared}
        raise RuntimeError("unavailable")

    app.ask = fail
    output = tmp_path / "evaluation.json"
    with pytest.raises(ValueError):
        evaluate(app, output)
    rows = json.loads(output.read_text())["results"]
    assert rows[0]["partial_trace"]["model_calls"][0]["question"] == rows[0]["question"]


def test_evaluation_accepts_additional_context_task(tmp_path):
    from minisense.agents import demo_plan
    from minisense.contracts import Task, Plan

    class AdditionalContext:
        def plan(self, question, latest):
            plan = demo_plan(question, latest)
            extra = Task(id="extra_rag", agent="rag", operation="retrieve", query="CSAT target")
            plan.tasks.insert(-1, extra)
            plan.tasks[-1].depends_on.append(extra.id)
            return Plan.model_validate(plan.model_dump())

    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    app.provider = AdditionalContext()
    assert evaluate(app, tmp_path / "evaluation.json")["questions"] == 3


def test_top_three_question_rejects_single_complaint_plan(tmp_path):
    from minisense.agents import demo_plan

    class TooFew:
        def plan(self, question, latest):
            plan = demo_plan(question, latest)
            if question.startswith("What are the top three"):
                plan.tasks[0].top_n = 1
            return plan

    app = Orchestrator(SurveyStore(generate(100)), FixtureIndex())
    app.provider = TooFew()
    with pytest.raises(ValueError, match="failed checks"):
        evaluate(app, tmp_path / "evaluation.json")
