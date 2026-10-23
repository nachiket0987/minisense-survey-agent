# Reference review

Reviewed 23 October 2026. Repositories were cloned read-only into a sibling
reference directory, not vendored into MiniSense. Commit IDs identify the inspected
snapshots. No application source was copied. All implementation is independent.
No license file was found in the four application repositories at these snapshots;
public visibility alone does not grant permission to copy. Patterns below are
conceptual influences, not claims that these repositories are dependencies.

## mahfuz-raihan/agentic-rag-system

URL: https://github.com/mahfuz-raihan/agentic-rag-system
Commit: 21c53233473e72fc309fb888e4d43853322fa7f8

Inspected `core/graph.py`, `core/state.py`, `core/ingestion.py`,
`agents/supervisor.py`, `agents/data_analyst.py`, `agents/text_rag.py`, and
`requirements.txt`. Supervisor selects tabular/RAG/general routes; state carries
question, documents and retry count; a critic can request query transformation.
The FAISS index is session-local and tabular data is held in a session store.
Useful: explicit specialist routing and retrieval before synthesis. Avoided:
`exec` of model-generated chart code with unrestricted builtins; the claimed
isolation is not a security sandbox. Unknown routes silently become general chat.
String route outputs and largely unchecked state would not meet our contracts.
Dependencies are broad lower bounds including LangChain 1.x, LangGraph 1.x,
Pandas 3.x and Chainlit; not compatible as a drop-in with the older references.
Decision: independently implement typed routing, in-memory data and local retrieval.

## ahmad2b/customer-feedback-analysis-ai-agent

URL: https://github.com/ahmad2b/customer-feedback-analysis-ai-agent
Commit: e985c57441785299f29f7994458e5daf574b215d

Inspected `agent-service/app/agent.py`, `state.py`, `tools.py`, `main.py`, and
`agent-service/pyproject.toml`. Separate categorization, sentiment, priority and
action nodes connect feedback to recommendations; PostgreSQL stores results.
Useful: preserve separate classification and action fields. Defect: assistant_node
reads `state.messages` while State declares no messages. `llm_with_tools = llm`
does not bind tools; naming alone is not function calling. Several outputs rely on
free-form strings and fallback categories. Database setup at startup and many
provider/search/weather dependencies are unnecessary here. Python 3.12,
LangChain 0.3/LangGraph 0.2 dependencies differ from reference 1.
Decision: use explicit annotation fields and validated tool execution, no code reuse.

## siddiquafathima/feedback-insights-pipeline-agent

URL: https://github.com/siddiquafathima/feedback-insights-pipeline-agent
Commit: 0acd0905a1196aa2a376d95c9bdde5c3969567a4

Inspected `app/agent/graph.py`, `app/analytics.py`, `app/llm_service.py`, and
`requirements.txt`. Pydantic extraction with bounded retry, SQL trend aggregation,
and conditional escalation through an MCP tool are relevant patterns. It genuinely
calls an MCP tool on escalation, unlike a prose-only action description.
Weakness: reasoning parses three text lines; invalid action becomes a fallback
rather than a validated task. `asyncio.run` requires care in async callers;
per-escalation tool discovery/subprocess startup is excessive for this assessment.
Provider is hardwired to a hosted NVIDIA model; free availability is not assumed.
LangChain 0.3/LangGraph 0.2 and MCP add avoidable moving parts.
Decision: independent allowlisted tools, bounded failures and traceable execution.

## ro-anderson/multi-agent-rag-customer-support

URL: https://github.com/ro-anderson/multi-agent-rag-customer-support
Commit: 86b17b603e0fd9d453203664134475d136f1c2ed

Inspected `customer_support_chat/app/graph.py`,
`vectorizer/app/embeddings/embedding_generator.py`,
`vectorizer/app/vectordb/chunkenizer.py`, and `pyproject.toml`. Primary assistant
routes to booking specialists; tool nodes separate safe from sensitive actions.
Vectorization is separated from the chat service. Useful: specialist boundaries,
explicit handoffs and independent ingestion. The actual domain is travel, not
survey analytics. OpenAI ada-002 embeddings, Qdrant and a larger graph are
unnecessary for seven FAQ sections. Character chunks (300/20) risk separating
policy qualifications. LangChain 0.2/LangGraph 0.2 pins cannot simply be merged
with the other repositories. Decision: independently implement section chunks and
local dense retrieval; no booking, databases or deployment infrastructure.

## DietrichGebert/ponytail

URL: https://github.com/DietrichGebert/ponytail
Commit: 09c434ab73ca43761c5d8b0c5d341926c2fba710
License: MIT, copyright (c) 2026 DietrichGebert.

Inspected `skills/ponytail/SKILL.md`, `skills/ponytail-review/SKILL.md`,
`package.json`, `LICENSE`, and README. Version 5.3.2 is an agent guidance/plugin
package, not a survey analysis runtime or an orchestration library. Applied its
smallest-complete-solution and connected-code review principles: prefer stdlib,
avoid unnecessary wrappers, keep trust-boundary validation, and test risky logic.
No skill/plugin files or runtime code are redistributed. No installation or
persistent skill modification was needed. Benchmark marketing claims were not
independently verified and are not claimed as MiniSense performance results.

## Identity, provenance and secret audit

Application maintainer: Nachiket Lohar. Connected GitHub username: psychochan.
No public contact email is placed in the application; the account email is not
assumed to be the preferred public contact. Git commits use the GitHub ID-based
noreply address. Original names and URLs appear only here and in README attribution.
No reference repository configuration, API credential, developer metadata or
branding was imported. No copied third-party source means no third-party source
license notice needs redistribution; dependencies retain their own upstream
licenses. MiniSense's original code is MIT licensed by its maintainer.

Final scan and review evidence will be recorded in `docs/verification.md`.
