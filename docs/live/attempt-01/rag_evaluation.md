# Executed RAG evaluation

Mode: llm; model: openai/gpt-oss-20b. Actual embedding retrieval. Full traces: `evaluation.json`.

validated extractive evidence; LLM orders facts and selects a supported recommendation

## What are the top three customer complaints in June 2026?

Status: failed

Agents: data, summary

In June 2026, b01 had 53,000 responses, a mean satisfaction rating of 3.36/5, and 45.82% rating four or five. The leading complaint themes were wait time (6,878; 12.98% of responses), food quality (4,713; 8.89% of responses), value (3,292; 6.21% of responses) [survey:t1]. Recommendation: investigate the leading reported themes and validate causes operationally before changing staffing or pricing.

### Retrieved chunks

Checks: {"expected_scope": true, "expected_routing": false, "expected_theme": true, "t1_count": true, "t1_mean": true, "t1_satisfied_pct": true, "t1_complaints": true, "t1_top_complaints": true, "t1_rates": true, "t1_tool_execution": true, "has_retrieved_context": false, "source_attribution": false, "retrieved_required_policy": false, "answer_grounded_policy": false, "evidence_preserved": true}
Dense retrieval ranks short complete policy sections. Required-policy and final-answer grounding checks are recorded separately. Other top-k sections may be tangential; the .25 cosine cutoff is heuristic. Survey complaints establish reported experience, not causes or actual wait durations.

## How did wait-time complaints change from May to June 2026, and what does the FAQ say about expected wait times?

Status: failed

Checks: {"completed": false}
Execution failed; inspect safe partial trace.

## How does current customer satisfaction compare with the company's CSAT target, and what action should management take?

Status: failed

Checks: {"completed": false}
Execution failed; inspect safe partial trace.
