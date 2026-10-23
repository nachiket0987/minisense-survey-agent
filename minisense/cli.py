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


from .evaluation import evaluate


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
    app.dataset_sha256 = hashlib.sha256(args.data.read_bytes()).hexdigest()
    if args.command == "ask":
        result = app.ask(args.question)
        print(
            result.model_dump_json(indent=2)
            if args.json
            else f"[{result.summary.mode}] {result.summary.answer}"
        )
    else:
        print(json.dumps(evaluate(app, args.output)))
