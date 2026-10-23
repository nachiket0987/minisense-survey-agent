"""Reproduce a small author-labeled challenge audit; not production validation.

From the repository root:
  python docs/finetuning/run_readiness_audit.py
Uses only the frozen local checkpoint, with no downloads or API calls.
"""
import hashlib
import json
import platform
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from minisense.finetune import predict

CASES = {
    "Positive-Food": ["The mushroom risotto was exquisite.", "I'd come back just for that delicious soup."],
    "Negative-Food": ["My chicken arrived raw in the middle.", "The noodles tasted of burnt oil."],
    "Negative-Wait": ["Forty minutes passed before anyone brought our drinks.", "We stood in line so long we nearly left."],
    "Positive-Staff": ["Our server patiently explained every ingredient.", "The cashier made us feel welcome."],
    "Negative-Staff": ["The waiter mocked my question.", "The cashier was rude when I asked for help."],
    "Negative-Order": ["I ordered a salad but received a burger.", "The takeaway bag was missing my dessert."],
    "Negative-Value": ["Twenty dollars for that tiny portion is a rip-off.", "The bill was far too high for what we got."],
    "Neutral-Other": ["We visited on Tuesday at noon.", "There were four people in our party."],
}
OOD = ["The parking garage charged too much.", "The restroom was filthy.",
       "My hotel room had bedbugs.", "asdf qwer zxcv 12345",
       "The food was excellent but the waiter insulted us and half the order was missing.",
       "La comida estaba deliciosa."]


def main():
    checkpoint = ROOT / ".cache/classifier-assessment"
    records = []
    for expected, texts in [*CASES.items(), (None, OOD)]:
        for text in texts:
            start = time.perf_counter()
            result = predict(str(checkpoint), text)
            records.append(dict(text=text, expected=expected, prediction=result,
                                cli_style_seconds=time.perf_counter() - start))
    scoped = [r for r in records if r["expected"] is not None]
    unknown = [r for r in records if r["expected"] is None]
    times = sorted(r["cli_style_seconds"] for r in records)
    report = dict(
        production_validated=False, deployment_ready=False,
        provenance="Assistant-authored synthetic challenge cases and labels; no independent human review",
        scope="Small diagnostic sample; not representative real data, a load test, or a production acceptance gate",
        checkpoint_sha256=hashlib.sha256((checkpoint / "model.safetensors").read_bytes()).hexdigest(),
        python=platform.python_version(), platform=platform.platform(),
        in_scope_count=len(scoped),
        in_scope_correct=sum(r["prediction"]["label"] == r["expected"] for r in scoped),
        in_scope_accepted_errors=sum(r["prediction"]["label"] is not None and r["prediction"]["label"] != r["expected"] for r in scoped),
        out_of_scope_or_ambiguous_count=len(unknown),
        out_of_scope_or_ambiguous_abstained=sum(r["prediction"]["abstained"] for r in unknown),
        latency=dict(measurement="Sequential predict calls, each reloads model/tokenizer; first includes imports. Not service latency.",
                     median_seconds=statistics.median(times), maximum_seconds=max(times)),
        cases=records,
    )
    # Preserve the committed pre-hardening historical audit on later reruns.
    target = ROOT / ".cache/readiness-audit-current.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
