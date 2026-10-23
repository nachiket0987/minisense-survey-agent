# MiniSense — Survey Analysis Agent

MiniSense answers business questions about 100,000 synthetic GreenLeaf Bistro
survey responses and a product FAQ. Built by **Nachiket Lohar** for the
**omniSense technical assessment**.

The CLI has a deterministic demo path and an OpenAI-compatible
LLM path. Demo mode uses **real sentence-transformers embeddings and dense vector
retrieval**, not a simulated retriever. Its planner and narrative renderer are
explicitly deterministic. Live Groq planning, API function calling, Python tool
execution and constrained synthesis are recorded separately in
[live evaluation](docs/live/rag_evaluation.md). See verification for actual results.
No paid service is invoked by default, and ChatGPT Plus is not an API credential.

## Features and architecture

- Pydantic task DAG with validated dependencies, filters and outputs.
- Orchestrator schedules DataAgent, ComparisonAgent, RAGAgent and SummaryAgent
  according to each plan; FAQ-only questions skip analytics, single months skip comparisons.
- DataAgent dispatches an allowlisted `compute_metrics` tool and records the
  internal `compute_csat` execution. LLM mode requests actual API function calls;
  demo mode makes deterministic structured calls. Numeric work runs in Python.
- Comparison includes count and mean differences, relative changes and complaint
  prevalence changes; zero denominators are null and small samples are flagged.
- Seven complete FAQ Q/A sections are embedded once and stored as normalized
  vectors in a NumPy flat cosine index. Query-time hash checks reject stale data.
- Summary receives structured survey results plus retrieved FAQ evidence. An LLM
  can order evidence and select a supported recommendation; validated extractive
  statements preserve numbers and policy qualifiers. This limits stylistic freedom
  in exchange for numerical reliability.

See [design](docs/design.md), [requirements](docs/requirements_matrix.md),
[reference review](docs/reference_review.md), and [verification](docs/verification.md).

## Prerequisites and installation

Python 3.12 (tested on Windows with 3.12.11), Git, internet for initial package/model
downloads, and enough disk space for PyTorch. No GPU is required for the demo.
Run commands from the repository root. On Windows, open that folder in VS Code,
open a PowerShell terminal, and select `.venv\Scripts\python.exe` as the interpreter.
Activation is optional, avoiding PowerShell execution-policy changes.

```powershell
# If Python 3.12 is installed:
py -3.12 -m venv .venv
# Otherwise, using uv (https://docs.astral.sh/uv/getting-started/installation/):
# uv python install 3.12 --install-dir .tools/python
# $pythonRoot = Get-ChildItem .tools/python -Directory -Filter 'cpython-3.12*' | Select-Object -First 1
# & "$($pythonRoot.FullName)/python.exe" -m venv .venv

# Run installations one at a time. uv 0.7.12 was used on this Windows machine.
uv pip install --python .venv/Scripts/python.exe torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.\.venv\Scripts\python.exe -m minisense generate
.\.venv\Scripts\python.exe -m minisense validate
.\.venv\Scripts\python.exe -m minisense ingest
.\.venv\Scripts\python.exe -m minisense ask "What are the top three customer complaints in June 2026?" --json
.\.venv\Scripts\python.exe -m minisense evaluate
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Both tested pip versions (25.0.1 and 26.2.2) encountered Windows `WinError 5`
while replacing SymPy RECORD metadata; uv completed the sequential installation.
Do not run competing installers in one environment. The installed dependency
snapshot is in [windows_environment.txt](docs/windows_environment.txt).

Linux/macOS: create the environment with `python3 -m venv .venv`, then replace the
Windows executable above with `.venv/bin/python`. On Linux the tested CPU wheel
is `torch==2.6.0+cpu`. The integration test loads/downloads the real embedding model;
unit tests use explicitly labeled embedding/provider mocks. Model downloads are
cached by Hugging Face. Ingestion no-ops for unchanged FAQ/model signatures.

The CLI is the runnable application; there is no web server or UI to start.
`python -m minisense --help` lists commands. Global options (`--data`, `--faq`,
`--index`, `--provider`) precede the subcommand. `ask --json` includes the full
plan, agents, tool calls, structured outputs, sources, scores and final narrative.

## Dataset and definitions

`generate` defaults to 100,000 records with seed 42: May 2026 has 47,000 and June
has 53,000. All records follow the assignment schema, correcting its invalid JSON
and inconsistent business name. Additional `sentiment`, `themes`, and
`complaint_themes` fields are synthetic ground-truth annotations. Mixed feedback
can contain a negative and positive mention. Templates generate varied feedback,
but do not approximate the full complexity of real customer language.

Rating is the satisfaction observation. **Mean CSAT = sum(rating)/count** out of
five. **Satisfied percentage = count(rating >= 4)/count × 100**, reported separately.
The FAQ's 4.5 target and below-4.0 review trigger apply to mean CSAT. A complaint
is an annotated negative mention, including mixed feedback. Prevalence divides by
all filtered responses; one response may mention multiple themes. Means and
percentages are undefined for empty samples. Dates are inclusive. “Current” means
June 2026, the latest dataset month, rather than the wall-clock month.

JSON is loaded and validated once per process; agents share it. Generated JSON,
vector indexes, environments and secrets are ignored by Git. The generator is the
canonical source, so the large dataset is intentionally regenerated after checkout.

## Examples and evaluation

```powershell
.\.venv\Scripts\python.exe -m minisense ask "How did wait-time complaints change from May to June 2026, and what does the FAQ say about expected wait times?"
.\.venv\Scripts\python.exe -m minisense ask "How does current customer satisfaction compare with the company's CSAT target, and what action should management take?"
```

Actual executed answers, retrieved text and retrieval observations are in
[the evaluation report](docs/rag_evaluation.md); full machine-readable plans,
tool traces, results and correctness checks are in [evaluation.json](docs/evaluation.json).
The evaluator checks expected scope/routing as well as independent calculations.
See [dataset validation](docs/dataset_validation.json) for counts and hash.

## Configuring an LLM

Use an authorized OpenAI-compatible server supporting JSON output and tool calls.
Groq's `openai/gpt-oss-20b` was confirmed through its authenticated model-list API
and tested on the user's approved free-tier account. Confirm your own free quota
before running. MiniSense neither enables billing nor switches to paid capacity.
`.env.example` documents settings; the app does not load `.env`.

```powershell
$env:MINISENSE_BASE_URL = "https://api.groq.com/openai/v1"
$env:MINISENSE_MODEL = "openai/gpt-oss-20b"
# If GROQ_API_KEY already exists in THIS process, map it without displaying it:
if ($env:GROQ_API_KEY) {
    $env:MINISENSE_API_KEY = $env:GROQ_API_KEY
} else {
    $secureKey = Read-Host "Groq API key (free-tier account)" -AsSecureString
    $env:MINISENSE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
    Remove-Variable secureKey
}
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m minisense --provider llm ask "What are the top three complaints in June 2026?" --json
.\.venv\Scripts\python.exe -m minisense --provider llm evaluate --output docs/live/evaluation.json
```

Run credential-dependent commands in the same terminal as this setup. Variables
set in VS Code's terminal do not necessarily reach Codex's separate shell. Codex
sign-in does not grant this application API access. Never paste keys into chat;
never echo them, put them in command arguments, or commit `.env`. No dotenv loader
or new configuration-precedence rule was introduced. For a local server, replace
the base URL/model and set a key only if required.

Compatibility is not assumed for every model. Invalid plans receive at most
three schema-validation attempts. Unrecognized tools, changed tool filters,
invalid evidence selections and unavailable providers fail explicitly rather than
falling back to a fabricated successful answer. Remote providers can charge fees;
the documented live runs used the user's explicitly approved free-tier account.
HTTP diagnostics omit response bodies and authentication headers. A 429 with a
numeric Retry-After of at most 60 seconds gets at most two retries; other quota
failures stop. Evaluation saves each question, including safe partial failures,
before continuing. Real model exchanges and Python executions are distinct fields.

## Fine tuning design

For 10,000 daily responses, I would first define eight mutually exclusive labels:
Positive–Food, Negative–Food, Negative–Wait, Positive–Staff, Negative–Staff,
Negative–Order, Negative–Value, and Neutral–Other. Mixed feedback receives the
most actionable negative label using a documented precedence rule; ambiguous
examples go to human review. This is an initial business taxonomy, not every
sentiment/topic combination. I would curate roughly 8,000–16,000 representative
examples, aiming initially for at least 500 per class and learning curves rather
than assuming a fixed data requirement. Sample across businesses, channels,
languages, lengths, and time periods. Remove personal information and duplicates.
Use GPT-4o for draft labels, human review for disagreements, and double-label a
subset to measure agreement. Include rare classes, negation, sarcasm, and mixed
feedback; preserve natural class prevalence in evaluation.

I would benchmark Qwen2.5-1.5B-Instruct against a smaller encoder classifier before
committing to a generative model. The 1.5B checkpoint offers open weights and an
Apache-2.0 license; I would verify the exact revision and license before release.
Its capacity may suffice for eight labels while reducing serving cost. Start with
LoRA when the model fits the available GPU; use four-bit QLoRA when memory is
constrained, after measuring quantization effects. Full fine-tuning is a baseline
only if adaptation quality justifies its larger memory and checkpoint cost. Our
Windows laptop is suitable for preparation and inference experiments, not assumed
to provide useful GPU training throughput. Any rented GPU requires a separate
approved budget; this submission runs no training job.

Use Hugging Face Transformers Trainer with PEFT, versioned JSONL records, a pinned
model revision, fixed seeds, bounded sequence length, gradient accumulation, and
checkpointed jobs. Split approximately 70/15/15 by business or conversation group
and chronology so near-duplicates cannot leak between sets. Tune class sampling
on training data only. Store dataset hashes, taxonomy version, hyperparameters,
and adapter artifacts with each run.

Track macro-F1, per-class precision/recall, confusion matrices, abstention rate,
invalid outputs, and performance by channel and language. Proposed release gates
are macro-F1 at least 0.90, critical negative-class recall at least 0.95, and no
material regression against the reviewed frontier baseline, with confidence
intervals and business sign-off. Also benchmark p95 latency, sustained throughput,
peak bursts, and cost per thousand responses; 10,000 daily responses average only
about 0.12 requests per second, so burst requirements drive capacity.

Serve a versioned adapter behind an isolated classification route. Shadow traffic,
then canary it; retain the existing model route and rollback switch. Monitor drift
and audit uncertain cases. Keep source connectors, canonical text records,
classification schema, training configuration, and serving serializers separate,
so input formats or label changes require adapters and versioning rather than
rewriting the training pipeline.

## Trade-offs and known limitations

Plain Python scheduling avoids LangGraph overhead for a short DAG. NumPy exact
search is appropriate for seven chunks; FAISS or a managed store becomes useful
for larger corpora. The .25 cosine cutoff is a heuristic and needs calibration.
Policy context cannot prove operational causes or actual wait durations. The demo
language parser supports whole-month questions, known themes and b01-style filters;
unsupported scopes fail where recognized. It is not a general natural-language
understanding system. Production text classification is proposed, not implemented;
analytics relies on synthetic annotations. Changes are descriptive, not causal
or statistically significant claims. Dataset generation is deterministic; model
embeddings may vary slightly across hardware/library revisions. No fine-tuning job
was performed. Windows runtime evidence is in docs/verification.md. The constrained
summary is a coherent paragraph built from validated statements: the model orders
evidence and selects a recommendation; it does not freely rewrite facts. This meets
the assignment's structured-output/narrative requirement with limited style.

## References and attribution

Conceptual references only; no application code was copied:

- https://github.com/mahfuz-raihan/agentic-rag-system
- https://github.com/ahmad2b/customer-feedback-analysis-ai-agent
- https://github.com/siddiquafathima/feedback-insights-pipeline-agent
- https://github.com/ro-anderson/multi-agent-rag-customer-support
- https://github.com/DietrichGebert/ponytail — simplicity and connected-code review guidance.

[Reference review](docs/reference_review.md) records commits, inspected files,
license findings and defects. Model sources:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 and
https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct (fine-tuning proposal only).
MiniSense's original source is MIT licensed. Dependencies and downloaded model
weights retain their upstream licenses. No public contact email is configured.

## Importing the delivered Git history

If this project was delivered as an archive rather than a remote repository,
`minisense-history.bundle` preserves incremental commits. From the extracted
archive's parent directory:

```powershell
git clone .\minisense-history.bundle minisense-from-history
cd minisense-from-history
git branch -m main
# After creating an empty repo in your GitHub account:
git remote add origin https://github.com/psychochan/minisense-survey-agent.git
git push -u origin main
```

Use an empty repository and do not force-push. The extracted source folder can
also be opened directly in VS Code; the bundle is only needed to recover history.
