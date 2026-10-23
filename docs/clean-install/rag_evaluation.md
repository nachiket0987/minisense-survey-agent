# Executed RAG evaluation

Mode: llm; model: openai/gpt-oss-20b. Actual embedding retrieval. Full traces: `evaluation.json`.

validated extractive evidence; LLM orders facts and selects a supported recommendation

## What are the top three customer complaints in June 2026?

Status: passed

Agents: data, rag, rag, summary

In June 2026, b01 had 53,000 responses, a mean satisfaction rating of 3.36/5, and 45.82% rating four or five. The leading complaint themes were wait time (6,878; 12.98% of responses), food quality (4,713; 8.89% of responses), value (3,292; 6.21% of responses) [survey:t1]. No relevant FAQ evidence for query 'b01 business context'; context for that query is unavailable. FAQ [faq.txt#faq-03]: All complaints are escalated to the shift manager within 15 minutes. Refunds or replacements are offered for quality issues. The manager records the issue, checks the affected order, and explains the resolution. Customers should keep their receipt where possible so the team can locate the transaction. Escalation time and food preparation time are separate measures and should never be combined in reporting. Recommendation: investigate the leading reported themes and validate causes operationally before changing staffing or pricing.

### Retrieved chunks

**faq.txt#faq-03** cosine=0.5280
Q: How do you handle complaints?
A: All complaints are escalated to the shift manager within 15 minutes. Refunds or replacements are offered for quality issues. The manager records the issue, checks the affected order, and explains the resolution. Customers should keep their receipt where possible so the team can locate the transaction. Escalation time and food preparation time are separate measures and should never be combined in reporting.

**faq.txt#faq-05** cosine=0.3661
Q: How are order accuracy and food quality checked?
A: Staff check the item, requested substitutions, and packaging before handing over an order. Quality concerns should be recorded by menu item and shift. Repeated reports should prompt a check of preparation and handover steps. A complaint is evidence of a customer's reported experience; it does not establish the cause without further investigation.

**faq.txt#faq-06** cosine=0.2807
Q: How do you manage cleanliness and staff service?
A: Dining tables are checked between parties and the counter is inspected throughout service. The shift manager reviews recurring cleanliness or staff-service feedback during team briefings. Coaching should use specific observations rather than assigning blame from an anonymous comment. Urgent safety concerns require immediate manager attention.

Checks: {"expected_scope": true, "expected_routing": true, "expected_theme": true, "requested_top_three": true, "t1_count": true, "t1_mean": true, "t1_satisfied_pct": true, "t1_complaints": true, "t1_top_complaints": true, "t1_rates": true, "t1_tool_execution": true, "has_retrieved_context": true, "source_attribution": true, "retrieved_required_policy": true, "answer_grounded_policy": true, "evidence_preserved": true}
Dense retrieval ranks short complete policy sections. Required-policy and final-answer grounding checks are recorded separately. Other top-k sections may be tangential; the .25 cosine cutoff is heuristic. Survey complaints establish reported experience, not causes or actual wait durations.

## How did wait-time complaints change from May to June 2026, and what does the FAQ say about expected wait times?

Status: passed

Agents: data, data, rag, comparison, summary

In May 2026, b01 had 47,000 responses, a mean satisfaction rating of 3.64/5, and 56.40% rating four or five. The leading complaint themes were wait time (3,056; 6.50% of responses) [survey:t1]. In June 2026, b01 had 53,000 responses, a mean satisfaction rating of 3.36/5, and 45.82% rating four or five. The leading complaint themes were wait time (6,878; 12.98% of responses) [survey:t3]. Between the compared periods, response volume changed by +6,000 (+12.77%), and mean rating changed by -0.28 points [comparison:t2]. From May 2026 to June 2026, wait time complaints changed by +3,822 (+125.07%); prevalence changed by +6.48 percentage points [comparison:t2]. FAQ [faq.txt#faq-02]: We target under 10 minutes for counter orders during off-peak hours. Peak hours (12–1 PM, 6–8 PM) may see 15–20 minute waits. These are operational targets and typical ranges, not measurements of every customer's actual wait. Staff should communicate expected delays at ordering and update customers when preparation takes longer. Survey complaints alone cannot establish the actual number of minutes waited or prove that a target was breached. Recommendation: investigate the leading reported themes and validate causes operationally before changing staffing or pricing.

### Retrieved chunks

**faq.txt#faq-02** cosine=0.6226
Q: What is your average wait time?
A: We target under 10 minutes for counter orders during off-peak hours. Peak hours (12–1 PM, 6–8 PM) may see 15–20 minute waits. These are operational targets and typical ranges, not measurements of every customer's actual wait. Staff should communicate expected delays at ordering and update customers when preparation takes longer. Survey complaints alone cannot establish the actual number of minutes waited or prove that a target was breached.

**faq.txt#faq-03** cosine=0.2951
Q: How do you handle complaints?
A: All complaints are escalated to the shift manager within 15 minutes. Refunds or replacements are offered for quality issues. The manager records the issue, checks the affected order, and explains the resolution. Customers should keep their receipt where possible so the team can locate the transaction. Escalation time and food preparation time are separate measures and should never be combined in reporting.

Checks: {"expected_scope": true, "expected_routing": true, "expected_theme": true, "t1_count": true, "t1_mean": true, "t1_satisfied_pct": true, "t1_complaints": true, "t1_top_complaints": true, "t1_rates": true, "t1_tool_execution": true, "t3_count": true, "t3_mean": true, "t3_satisfied_pct": true, "t3_complaints": true, "t3_top_complaints": true, "t3_rates": true, "t3_tool_execution": true, "comparison_dependencies": true, "comparison_count_delta": true, "comparison_rate_delta": true, "comparison_relative_change": true, "has_retrieved_context": true, "source_attribution": true, "retrieved_required_policy": true, "answer_grounded_policy": true, "evidence_preserved": true}
Dense retrieval ranks short complete policy sections. Required-policy and final-answer grounding checks are recorded separately. Other top-k sections may be tangential; the .25 cosine cutoff is heuristic. Survey complaints establish reported experience, not causes or actual wait durations.

## How does current customer satisfaction compare with the company's CSAT target, and what action should management take?

Status: passed

Agents: data, rag, rag, summary

In June 2026, b01 had 53,000 responses, a mean satisfaction rating of 3.36/5, and 45.82% rating four or five. The leading complaint themes were wait time (6,878; 12.98% of responses), food quality (4,713; 8.89% of responses), value (3,292; 6.21% of responses) [survey:t1]. FAQ [faq.txt#faq-04]: We aim for a CSAT of 4.5+. Scores below 4.0 trigger a root-cause review with the operations team. For this demonstration, CSAT means the mean satisfaction rating on a one-to-five scale. A separate satisfied-response percentage counts ratings of four or five, but the 4.5 target does not apply to that percentage. Operations should inspect response volumes and recurring themes before selecting improvements; falling short of 4.5 does not automatically mean the below-4.0 review rule applies. No relevant FAQ evidence for query 'business context'; context for that query is unavailable. The latest mean is 1.14 points below the FAQ target of 4.50/5. Recommendation: initiate the documented operations root-cause review because the mean is below 4.0.

### Retrieved chunks

**faq.txt#faq-04** cosine=0.5673
Q: What is your CSAT target?
A: We aim for a CSAT of 4.5+. Scores below 4.0 trigger a root-cause review with the operations team. For this demonstration, CSAT means the mean satisfaction rating on a one-to-five scale. A separate satisfied-response percentage counts ratings of four or five, but the 4.5 target does not apply to that percentage. Operations should inspect response volumes and recurring themes before selecting improvements; falling short of 4.5 does not automatically mean the below-4.0 review rule applies.

Checks: {"expected_scope": true, "expected_routing": true, "expected_theme": true, "t1_count": true, "t1_mean": true, "t1_satisfied_pct": true, "t1_complaints": true, "t1_top_complaints": true, "t1_rates": true, "t1_tool_execution": true, "target_trigger": true, "has_retrieved_context": true, "source_attribution": true, "retrieved_required_policy": true, "answer_grounded_policy": true, "evidence_preserved": true}
Dense retrieval ranks short complete policy sections. Required-policy and final-answer grounding checks are recorded separately. Other top-k sections may be tangential; the .25 cosine cutoff is heuristic. Survey complaints establish reported experience, not causes or actual wait durations.
