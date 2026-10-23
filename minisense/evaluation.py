"""Independent checks and incremental evidence for canonical assessment runs."""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from .contracts import Plan, THEMES

POLICIES = ("Q: How do you handle complaints?", "Q: What is your average wait time?", "Q: What is your CSAT target?")


def retrieval_observation(results, number):
    matches, adjacent, empty = [], [], []
    for value in results.values():
        if "chunks" not in value:
            continue
        if not value["chunks"]:
            empty.append(value["query"])
        for rank, chunk in enumerate(value["chunks"], 1):
            if POLICIES[number] in chunk["content"]:
                score = "unavailable" if chunk.get("score") is None else f'{chunk["score"]:.4f}'
                matches.append(f'{chunk["id"]} at rank {rank} (cosine {score})')
            else:
                adjacent.append(chunk["id"])
    text = ("Required policy retrieved: " + "; ".join(matches) + ". " if matches
            else "Required policy was not retrieved; the answer cannot be grounded in that policy. ")
    if adjacent:
        text += "Other returned sections: " + ", ".join(dict.fromkeys(adjacent)) + "; these offer adjacent context rather than direct evidence for the requested policy. "
    if empty:
        text += "No chunk passed the threshold for queries: " + ", ".join(repr(q) for q in empty) + ". "
    text += (
        "Complaint-handling policy supports escalation and quality remedies; the complaint ranking comes from survey counts, not FAQ text."
        if number == 0 else
        "The wait policy distinguishes off-peak targets and peak ranges; survey complaints contain no measured wait durations and cannot prove a target breach."
        if number == 1 else
        "The CSAT policy supplies the 4.5 mean-rating target and below-4.0 review trigger; neither threshold applies to the satisfied-response percentage."
    )
    return text + " The .25 cosine cutoff is heuristic; these three examples do not establish general retrieval accuracy."


def check_answer(app, answer, number):
    invoked = Counter(answer.agents_invoked)
    data = sorted((t for t in answer.plan.tasks if t.agent == "data"),
                  key=lambda t: t.period.start)
    periods = [("2026-05-01", "2026-05-31"), ("2026-06-01", "2026-06-30")]
    expected = periods if number == 1 else periods[1:]
    checks = {
        "expected_scope": [(str(t.period.start), str(t.period.end)) for t in data] == expected
        and all(t.business_id == "b01" for t in data),
        "expected_routing": invoked["data"] == (2 if number == 1 else 1)
        and invoked["comparison"] == (1 if number == 1 else 0)
        and invoked["summary"] == 1 and invoked["rag"] >= 1
        and invoked == Counter(t.agent for t in answer.plan.tasks),
        "expected_theme": bool(data) and all(
            t.theme in (None, "wait_time") if number == 1 else
            t.theme in (None, "satisfaction") if number == 2 else t.theme is None
            for t in data),
    }
    # Revalidate mutable models and verify dependencies, rather than task-list order.
    Plan.model_validate(answer.plan.model_dump())
    if number == 0:
        checks["requested_top_three"] = len(data) == 1 and data[0].top_n == 3
    for task in data:
        actual = answer.results.get(task.id, {})
        raw = app.store.select(task.period, task.business_id)
        counts = Counter(t for r in raw for t in r.complaint_themes)
        names = [task.theme] if task.theme else THEMES
        complaints = {t: counts[t] for t in names}
        top = sorted(((t, n) for t, n in complaints.items() if n),
                     key=lambda x: (-x[1], x[0]))[:task.top_n]
        mean = sum(r.rating for r in raw) / len(raw) if raw else None
        satisfied = 100 * sum(r.rating >= 4 for r in raw) / len(raw) if raw else None
        checks[f"{task.id}_count"] = actual.get("count") == len(raw)
        checks[f"{task.id}_mean"] = actual.get("mean_rating") == mean
        checks[f"{task.id}_satisfied_pct"] = actual.get("satisfied_pct") == satisfied
        checks[f"{task.id}_complaints"] = actual.get("complaints") == complaints
        checks[f"{task.id}_top_complaints"] = actual.get("top_complaints") == [list(x) for x in top]
        checks[f"{task.id}_rates"] = actual.get("complaint_rates") == {
            t: 100 * n / len(raw) if raw else None for t, n in complaints.items()}
        checks[f"{task.id}_tool_execution"] = any(
            call.name == "compute_metrics" and call.arguments.get("period") == task.period.model_dump(mode="json")
            and call.arguments.get("business_id") == task.business_id
            and call.result == actual for call in answer.tool_calls)
    if number == 1:
        comparisons = [t for t in answer.plan.tasks if t.agent == "comparison"]
        checks["comparison_dependencies"] = len(data) == 2 and len(comparisons) == 1 and comparisons[0].depends_on == [t.id for t in data]
        change = (answer.results.get(comparisons[0].id, {}).get("complaints", {}).get("wait_time", {})
                  if comparisons else {})
        if len(data) == 2:
            before, after = (app.store.select(t.period, "b01") for t in data)
            b = sum("wait_time" in r.complaint_themes for r in before)
            a = sum("wait_time" in r.complaint_themes for r in after)
            checks["comparison_count_delta"] = change.get("count_delta") == a - b
            checks["comparison_rate_delta"] = bool(before and after) and abs(
                (change.get("rate_delta_pp") or 0) - (100 * a / len(after) - 100 * b / len(before))) < 1e-10
            expected_change = 100 * (a - b) / b if b else None
            checks["comparison_relative_change"] = change.get("change_pct") == expected_change
        else:
            checks["comparison_results"] = False
    if number == 2:
        current = app.store.select(data[-1].period, "b01") if data else []
        mean = sum(r.rating for r in current) / len(current) if current else None
        recommendation = answer.summary.recommendation or ""
        checks["target_trigger"] = mean is not None and (
            "below 4.0" in recommendation if mean < 4 else "root-cause review because" not in recommendation)
    chunks = [c for v in answer.results.values() if "chunks" in v for c in v["chunks"]]
    checks["has_retrieved_context"] = bool(chunks)
    checks["source_attribution"] = bool(chunks) and all(
        c["source"] == "faq.txt" and c["id"].startswith("faq-") for c in chunks)
    policy = POLICIES[number]
    # Presence in retrieval alone is insufficient: the final answer must use it.
    relevant = [c for c in chunks if policy in c["content"]]
    checks["retrieved_required_policy"] = bool(relevant)
    checks["answer_grounded_policy"] = any(
        c["content"].split("\nA:", 1)[-1].strip() in answer.summary.answer
        and f'[{c["source"]}#{c["id"]}]' in answer.summary.answer for c in relevant)
    checks["evidence_preserved"] = all(fact in answer.summary.answer for fact in answer.summary.evidence)
    return checks


def write_report(app, output, records):
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "llm" if app.provider else "demo",
        "model": getattr(app.provider, "model", None),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "embedding": "actual sentence-transformers embeddings; no keyword replacement",
        "dataset_sha256": getattr(app, "dataset_sha256", None),
        "synthesis": "validated extractive evidence; LLM orders facts and selects a supported recommendation",
        "results": records,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, output)


def write_markdown(payload, output):
    records = payload["results"]
    markdown = ["# Executed RAG evaluation", "", f'Mode: {payload["mode"]}; model: {payload["model"]}. Actual embedding retrieval. Full traces: `{output.name}`.', "", payload["synthesis"], ""]
    for record in records:
        markdown += [f'## {record["question"]}', "", f'Status: {record["status"]}', ""]
        if "summary" in record:
            markdown += [f'Agents: {", ".join(record["agents_invoked"])}', "", record["summary"]["answer"], "", "### Retrieved chunks", ""]
        for value in record.get("results", {}).values():
            for chunk in value.get("chunks", []):
                score = "unavailable" if chunk["score"] is None else f'{chunk["score"]:.4f}'
                markdown += [f'**{chunk["source"]}#{chunk["id"]}** cosine={score}', chunk["content"], ""]
        markdown += ["Checks: " + json.dumps(record["correctness_checks"]), record.get("retrieval_observation", "Execution failed; inspect safe partial trace."), ""]
    output.with_name("rag_evaluation.md").write_text("\n".join(markdown), encoding="utf-8")


def evaluate(app, output: Path):
    from .cli import QUESTIONS

    records = []
    for number, question in enumerate(QUESTIONS):
        try:
            answer = app.ask(question)
            record = answer.model_dump(mode="json")
            checks = check_answer(app, answer, number)
            record.update(question=question, correctness_checks=checks,
                          status="passed" if all(checks.values()) else "failed")
            record["retrieval_observation"] = retrieval_observation(answer.results, number)
        except (ValueError, RuntimeError, KeyError, IndexError, TypeError, FileNotFoundError) as exc:
            record = {"question": question, "status": "failed", "error_type": type(exc).__name__,
                      "correctness_checks": {"completed": False},
                      "partial_trace": deepcopy(getattr(app, "last_trace", {}))}
        records.append(record)
        # A later failure must not discard earlier successful executions.
        write_report(app, output, records)
    if not all(all(r["correctness_checks"].values()) for r in records):
        raise ValueError("Evaluation has failed checks; inspect saved evidence")
    return {"questions": len(records),
            "checks_passed": sum(len(r["correctness_checks"]) for r in records),
            "mode": "llm" if app.provider else "demo"}
