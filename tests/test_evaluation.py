from minisense.cli import evaluate
from minisense.agents import Orchestrator
from minisense.analytics import SurveyStore
from minisense.dataset import generate
from minisense.contracts import Retrieval, Chunk
import json
import pytest


class FixtureIndex:
    def retrieve(self, query, **kwargs):
        return Retrieval(
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
            ],
        )


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
