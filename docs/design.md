# MiniSense design

Maintainer: Nachiket Lohar. Context: omniSense technical assessment.

## Decisions

Use Python 3.12, Pydantic contracts, a CLI, a small dependency-aware scheduler,
sentence-transformers/all-MiniLM-L6-v2 embeddings, and a persisted NumPy cosine
index. Exact exhaustive vector search is equivalent to a flat vector store and
simpler than FAISS for approximately ten FAQ sections. No keyword retrieval fallback.

LangGraph would offer durable graph state and visualization, but adds dependencies
without improving this short, acyclic workflow. Plain Python keeps agent contracts
and actual scheduling visible. A configurable OpenAI-compatible provider generates
validated plans and function calls. It is optional to install a local compatible
server; no paid service is invoked by default. A separately labeled deterministic
`demo` planner and evidence renderer exercise analytics and retrieval without an
LLM. Demo execution is not evidence of live LLM integration.

The orchestrator validates a task DAG and dispatches only requested specialists.
DataAgent executes allowlisted, schema-validated analytics tool calls; in LLM mode
it asks the provider for actual function calls. ComparisonAgent consumes two data
results. RAGAgent returns attributed chunks. SummaryAgent receives structured
metrics, comparisons, and retrieved evidence in a synthesis prompt. To preserve
numbers, it renders validated evidence statements; an LLM may choose their order
and a supported recommendation, but cannot rewrite numeric statements.

## Data and definitions

Generate 100,000 JSON records using seed 42 across May and June 2026, with uneven
monthly volume. GreenLeaf Bistro is the only business. Ratings are CSAT observations:
report mean rating out of five and separately the percentage rating four or five.
The FAQ's 4.5 target and 4.0 review threshold apply to the mean. Empty means and
percentages are null. Dates are inclusive; current means latest dataset month.

Additional fields `sentiment`, `themes`, and `complaint_themes` are generator ground
truth. Analytics uses these explicit synthetic annotations rather than pretending
to classify arbitrary text perfectly. Negative mentions in mixed feedback count;
each theme counts at most once per response. Theme prevalence uses all filtered
responses as denominator. Multiple themes may make totals exceed response count.
Counts are exact for annotations, not claims about real-world semantic accuracy.

Compare raw counts, relative count changes, complaint prevalence in percentage
points, and mean rating. Undefined relative changes are null, never infinity.
Sample sizes below 30 are flagged; changes are descriptive, not causal or formal
statistical significance tests. No response text is executed as code.

## Retrieval and evidence

Keep each question and answer together. These short sections fit the embedding
model's input window and avoid splitting policy qualifications. Store normalized
vectors and metadata with model ID and FAQ SHA256. Ingestion is repeatable and
no-ops on unchanged inputs; query refuses stale indexes. Top-k results below a
configurable cosine threshold are removed. This threshold is a heuristic, not a
calibrated relevance probability. Citations identify source and section. The final narrative quotes the highest-scoring section in full; all top-k chunks remain in structured evidence and the synthesis prompt. Only
retrieved policy sections may support recommendations; absent evidence is stated.

## Boundaries and limitations

The demo grammar supports explicit months, two-month comparisons, known themes,
CSAT and FAQ requests, and b01 filters; unsupported requests fail. LLM mode handles
more language variation but must obey the same contracts. No arbitrary SQL,
Python execution, web browsing, UI, microservices, or training job. JSON is loaded
and validated once per process, with in-memory filtering; CLI invocations reload,
but agents within an invocation share the store. Larger or multi-user deployments
should use a database. Model downloads require network access; runtime provider
availability and costs belong to the user's configured endpoint.
