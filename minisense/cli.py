import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from .dataset import write_dataset
from .analytics import SurveyStore
from .agents import Orchestrator
from .provider import LLMProvider
from .retrieval import FAQIndex

QUESTIONS = [
    "What are the top three customer complaints in June 2026?",
    "How did wait-time complaints change from May to June 2026, and what does the FAQ say about expected wait times?",
    "How does current customer satisfaction compare with the company's CSAT target, and what action should management take?",
]


def validate_dataset(path):
    store = SurveyStore.load(path)
    months = dict(sorted(Counter(r.date.strftime("%Y-%m") for r in store.rows).items()))
    if len(store.rows) != 100000 or months != {"2026-05": 47000, "2026-06": 53000}:
        raise ValueError(
            "Assessment dataset requires exactly 100000 rows: May=47000, June=53000"
        )
    if any(
        r.business_id != "b01" or r.business_name != "GreenLeaf Bistro"
        for r in store.rows
    ):
        raise ValueError("Unexpected business contamination")
    sentiments = Counter(r.sentiment for r in store.rows)
    if len(sentiments) != 4:
        raise ValueError("Missing feedback sentiment variation")
    return {
        "count": len(store.rows),
        "months": months,
        "sentiments": dict(sentiments),
        "unique_texts": len({r.free_text for r in store.rows}),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def evaluate(app, output: Path):
    outputs = []
    for question in QUESTIONS:
        answer = app.ask(question)
        record = answer.model_dump(mode="json")
        checks = {}
        number = QUESTIONS.index(question)
        data_tasks = [t for t in answer.plan.tasks if t.agent == "data"]
        expected_periods = (
            [("2026-05-01", "2026-05-31"), ("2026-06-01", "2026-06-30")]
            if number == 1
            else [("2026-06-01", "2026-06-30")]
        )
        actual_periods = [(str(t.period.start), str(t.period.end)) for t in data_tasks]
        checks["expected_scope"] = actual_periods == expected_periods and all(
            t.business_id == "b01" for t in data_tasks
        )
        checks["expected_routing"] = answer.agents_invoked == (
            ["data", "data", "rag", "comparison", "summary"]
            if number == 1
            else ["data", "rag", "summary"]
        )
        checks["expected_theme"] = all(
            t.theme == ("wait_time" if number == 1 else None) for t in data_tasks
        )
        if number == 1 and any(t.agent == "comparison" for t in answer.plan.tasks):
            before = app.store.select(data_tasks[0].period, "b01")
            after = app.store.select(data_tasks[1].period, "b01")
            b = sum("wait_time" in r.complaint_themes for r in before)
            a = sum("wait_time" in r.complaint_themes for r in after)
            comparison_id = next(
                t.id for t in answer.plan.tasks if t.agent == "comparison"
            )
            change = answer.results[comparison_id]["complaints"]["wait_time"]
            checks["comparison_count_delta"] = change["count_delta"] == a - b
            checks["comparison_rate_delta"] = (
                abs(
                    change["rate_delta_pp"]
                    - (100 * a / len(after) - 100 * b / len(before))
                )
                < 1e-10
            )
            checks["comparison_relative_change"] = (
                abs(change["change_pct"] - 100 * (a - b) / b) < 1e-10
            )
        if number == 2:
            current = app.store.select(data_tasks[-1].period, "b01")
            mean = sum(r.rating for r in current) / len(current)
            checks["target_trigger"] = (
                ("below 4.0" in (answer.summary.recommendation or ""))
                if mean < 4
                else "root-cause review because"
                not in (answer.summary.recommendation or "")
            )
        for task in answer.plan.tasks:
            if task.agent == "data":
                actual = answer.results[task.id]
                raw = app.store.select(task.period, task.business_id)
                checks[f"{task.id}_count"] = actual["count"] == len(raw)
                checks[f"{task.id}_mean"] = (
                    abs(actual["mean_rating"] - sum(r.rating for r in raw) / len(raw))
                    < 1e-12
                    if raw
                    else actual["mean_rating"] is None
                )
                checks[f"{task.id}_complaints"] = all(
                    n == sum(t in r.complaint_themes for r in raw)
                    for t, n in actual["complaints"].items()
                )
        retrieved = [
            c for v in answer.results.values() if "chunks" in v for c in v["chunks"]
        ]
        checks["has_retrieved_context"] = bool(retrieved)
        checks["source_attribution"] = all(
            c["source"] == "faq.txt" and c["id"].startswith("faq-") for c in retrieved
        )
        if question == QUESTIONS[1]:
            checks["retrieved_wait_policy"] = any(
                "Q: What is your average wait time?" in c["content"] for c in retrieved
            )
        if question == QUESTIONS[2]:
            checks["retrieved_csat_policy"] = any(
                "Q: What is your CSAT target?" in c["content"] for c in retrieved
            )
        record["correctness_checks"] = checks
        record["retrieval_observation"] = (
            "Dense retrieval returned policy context; cosine similarity is heuristic. FAQ text explains policy, not causes or measured wait durations. See checks for target section presence."
        )
        outputs.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "mode": "llm" if app.provider else "demo",
                "embedding": "actual sentence-transformers embeddings; no keyword replacement",
                "results": outputs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown = [
        "# Executed RAG evaluation",
        "",
        f'Mode: {"LLM" if app.provider else "deterministic demo; no live LLM claim"}. Actual embedding retrieval. Full traces: `evaluation.json`.',
        "",
    ]
    for record in outputs:
        markdown += [
            f'## {record["plan"]["question"]}',
            "",
            f'Agents: {", ".join(record["agents_invoked"])}',
            "",
            record["summary"]["answer"],
            "",
            "### Retrieved chunks",
            "",
        ]
        for value in record["results"].values():
            if "chunks" in value:
                for c in value["chunks"]:
                    score = "unavailable" if c["score"] is None else f'{c["score"]:.4f}'
                    markdown += [
                        f'**{c["source"]}#{c["id"]}** cosine={score}',
                        c["content"],
                        "",
                    ]
        markdown += [
            "Checks: " + json.dumps(record["correctness_checks"]),
            record["retrieval_observation"],
            "",
        ]
    output.with_name("rag_evaluation.md").write_text(
        "\n".join(markdown), encoding="utf-8"
    )
    if not all(all(r["correctness_checks"].values()) for r in outputs):
        raise ValueError("Evaluation has failed checks; inspect saved evidence")
    return {
        "questions": len(outputs),
        "checks_passed": sum(len(r["correctness_checks"]) for r in outputs),
        "mode": "llm" if app.provider else "demo",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="MiniSense — Survey Analysis Agent")
    parser.add_argument("--data", type=Path, default=Path("data/responses.json"))
    parser.add_argument("--faq", type=Path, default=Path("data/faq.txt"))
    parser.add_argument("--index", type=Path, default=Path("data/index"))
    parser.add_argument(
        "--provider",
        choices=["demo", "llm"],
        default=os.getenv("MINISENSE_PROVIDER", "demo"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--count", type=int, default=100000)
    generate.add_argument("--seed", type=int, default=42)
    sub.add_parser("validate")
    sub.add_parser("ingest")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--json", action="store_true")
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--output", type=Path, default=Path("docs/evaluation.json"))
    args = parser.parse_args(argv)
    if args.command == "generate":
        write_dataset(args.data, args.count, args.seed)
        print(
            json.dumps(
                {"generated": args.count, "seed": args.seed, "path": str(args.data)}
            )
        )
        return
    if args.command == "validate":
        print(json.dumps(validate_dataset(args.data)))
        return
    index = FAQIndex(args.faq, args.index)
    if args.command == "ingest":
        print(json.dumps({"rebuilt": index.ingest()}))
        return
    app = Orchestrator(
        SurveyStore.load(args.data),
        index,
        LLMProvider() if args.provider == "llm" else None,
    )
    if args.command == "ask":
        result = app.ask(args.question)
        print(
            result.model_dump_json(indent=2)
            if args.json
            else f"[{result.summary.mode}] {result.summary.answer}"
        )
    else:
        print(json.dumps(evaluate(app, args.output)))
