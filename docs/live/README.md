# Live execution evidence

These files contain actual Groq API calls using openai/gpt-oss-20b, real Python
analytics and actual all-MiniLM-L6-v2 retrieval. The user approved their existing
free-tier credential; it was mapped between environment variable names within
each execution shell, never saved to a dotenv file or included in artifacts.

`evaluation.json` and `rag_evaluation.md` describe the latest complete assessment
run. `model_calls` records requests and returned content/function calls; `tool_calls`
records actual Python executions/results. Model reasoning and authentication
headers are excluded. This is constrained extractive synthesis: the model chooses
evidence order and a supported recommendation; Python preserves numeric facts and
full policy qualifications. It is not unrestricted prose generation.

Rejected runs are retained in attempt-01 through attempt-03. They demonstrate
omitted retrieval, malformed plans, free-tier throttling, an overly strict routing
check and an omitted evidence item. None is labeled successful. Attempt-01 exposed
a shared mutable trace buffer: its second question's model_calls were overwritten
by the third question before saving. Treat that particular partial model trace as
unreliable; the defect was reproduced and fixed with deep snapshots. Later traces
retain independent question histories.

Historical demo artifacts in the parent docs directory are preserved. No fine
tuning or paid capacity was enabled. See ../verification.md for commands, tests,
review and clean-install results.
