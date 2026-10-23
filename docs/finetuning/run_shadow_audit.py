"""Offline reusable-runtime audit; assistant-labeled synthetic data only."""
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from minisense.classifier_runtime import ClassifierRuntime
from docs.finetuning.run_readiness_audit import CASES, OOD

FRESH = {
    "Positive-Food": "The lemon tart tasted wonderful.",
    "Negative-Food": "The steak was tough and inedible.",
    "Negative-Wait": "An hour went by before our meals arrived.",
    "Positive-Staff": "Our waitress was thoughtful and kind.",
    "Negative-Staff": "The manager shouted at us.",
    "Negative-Order": "They forgot the fries that I ordered.",
    "Negative-Value": "The portion was tiny for such a high price.",
    "Neutral-Other": "Our reservation was for six o'clock.",
}


def main():
    checkpoint = ROOT / ".cache/classifier-assessment"
    start = time.perf_counter()
    runtime = ClassifierRuntime(checkpoint)
    startup = time.perf_counter() - start
    records = []
    cases = [("original", label, text) for label, texts in CASES.items() for text in texts]
    cases += [("original_ood", None, text) for text in OOD]
    cases += [("fresh", label, text) for label, text in FRESH.items()]
    for source, expected, text in cases:
        start = time.perf_counter()
        prediction = runtime.predict(text)
        records.append(dict(source=source, text=text, expected=expected,
                            prediction=prediction, seconds=time.perf_counter() - start))
    rejected = []
    for text in ("", "food " * 150, "a" * 10001):
        try:
            runtime.predict(text)
        except ValueError as exc:
            rejected.append(str(exc))
    original = [r for r in records if r["source"] == "original"]
    fresh = [r for r in records if r["source"] == "fresh"]
    report = dict(production_validated=False, mode="shadow",
                  provenance="Assistant-authored synthetic cases, not real-data validation",
                  checkpoint_sha256=hashlib.sha256((checkpoint / "model.safetensors").read_bytes()).hexdigest(),
                  original_candidate_correct=sum(r["expected"] == r["prediction"]["candidate_label"] for r in original),
                  original_count=len(original), fresh_count=len(fresh),
                  fresh_candidate_correct=sum(r["expected"] == r["prediction"]["candidate_label"] for r in fresh),
                  reviewed_count=sum(r["prediction"]["review_required"] for r in records),
                  automatic_decisions=sum(r["prediction"]["label"] is not None for r in records),
                  input_rejections=rejected, startup_seconds=startup,
                  warm_median_seconds=statistics.median(r["seconds"] for r in records),
                  timing_scope="Sequential local CPU, one model instance; not concurrent service load",
                  cases=records)
    assert report["automatic_decisions"] == 0 and len(rejected) == 3
    (ROOT / "docs/finetuning/shadow_audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
