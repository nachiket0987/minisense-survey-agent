# Design points to explain

- The orchestrator produces a validated task DAG, not a fixed sequence. Data,
  retrieval and comparison return typed results; summary depends on its evidence.
  Single-period questions avoid period comparison. Independent tasks may appear
  in different orders without changing correctness.
- A real model emits compute_metrics function arguments. DataAgent validates the
  function name and requires its filters to equal the approved task scope before
  Python computes anything. Model API requests and Python executions have separate
  traces. A model saying it called a tool would not satisfy this contract.
- Rating is the CSAT observation. June's mean is 3.3624/5; 45.8208% rated four or
  five. The FAQ's 4.5 target and below-4.0 trigger apply to the mean. Counts and
  complaint prevalence answer different questions when response volumes change.
- Seven complete FAQ Q/A sections preserve policy qualifications. Local normalized
  embeddings plus NumPy exact cosine search are sufficient for seven vectors;
  adding a managed database or graph framework would add setup without improving
  this assessment. The retrieval threshold is heuristic, not a probability.
- The LLM receives exact metrics and retrieved passages, orders complete evidence
  statements and chooses a supported recommendation. Python preserves numbers and
  policy qualifiers. This intentionally trades stylistic freedom for auditability;
  the final paragraph is constrained synthesis, not unrestricted generation.
- Synthetic theme annotations make evaluation reproducible but do not demonstrate
  a classifier's performance on real feedback. Survey complaints do not prove
  causes, actual waiting minutes, or representative population-level sentiment.
- JSON schema validation is necessary but cannot prove semantic correctness.
  Independent evaluation checks dates, business filters, requested cardinality,
  statistics, comparison dependencies, actual tool outputs and cited policy use.
  Invalid plans/selections get bounded correction; failures remain failures.
- Fine tuning is a 424-word design, not an executed training job. Human-reviewed
  labels, leakage-resistant splits, macro-F1 and critical-class recall gates would
  come before shadow/canary rollout of a versioned adapter.
