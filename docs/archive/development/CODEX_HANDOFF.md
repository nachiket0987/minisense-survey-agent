# MiniSense continuation brief

Continuation status: Windows setup, real Groq integration, latest 55-test suite and all
three live questions (58 checks) are verified. See verification.md and live/ for
current evidence. User changed the published repository to
https://github.com/nachiket0987/minisense-survey-agent (`implementation`). The
original snapshot below is preserved for provenance; its missing-provider and
missing-remote statements describe the handoff, not current status.

## Mission and authorization

Act as the implementing engineer and reviewer. Finish the existing omniSense
technical assessment; do not rebuild it. User authorizes routine implementation,
debugging, local setup, tests, documentation, incremental commits and publishing
the intended assessment repository. Ask only for unavailable credentials/account
permissions, paid-service approval, destructive actions or an unavoidable material
choice. Never use credentials from prior conversations or expose secrets.

Project maintainer: Nachiket Lohar. Connected GitHub account previously verified:
psychochan (ID 46772356). Intended repository name: minisense-survey-agent.
No preferred public contact email was supplied; omit it. Existing commits use the
GitHub noreply identity. Confirm current GitHub access before publishing.

Read in order:
1. docs/Assignment.docx, all text and tables including appendices (authoritative).
2. docs/requirements_matrix.md and docs/design.md.
3. README.md and docs/verification.md.
4. minisense/contracts.py, agents.py, analytics.py, provider.py, retrieval.py,
   cli.py, dataset.py and tests.
5. docs/evaluation.json, docs/rag_evaluation.md and docs/reference_review.md.

The code and tests are the actual implementation. If any prose differs, investigate
and correct the inconsistency; do not assume a historical completion claim proves
current runtime behavior.

## Existing implementation

Python CLI, Pydantic contracts, a dependency-aware task scheduler, four specialist
agents, shared in-memory survey data, exact analytics and a persisted normalized
NumPy cosine index. Real embeddings use sentence-transformers/all-MiniLM-L6-v2.
LangGraph and FAISS were deliberately omitted at this small scale. No UI/server,
external database or training job is required by the original assignment.

The demo planner is a limited deterministic grammar. The LLM provider requests
validated JSON plans, actual API function calls for compute_metrics, and a
structured selection of evidence for synthesis. Summary wording is currently
rendered from deterministic evidence statements and full quoted policy text; the
LLM orders evidence and selects an allowed recommendation. Describe this honestly.
If stronger generative synthesis is needed for assessment credibility, implement
it with evidence/numerical checks and explicit tests rather than merely renaming
the current renderer or changing its mode label.

The dataset has exactly 100,000 records, seed 42, May=47,000 and June=53,000,
all GreenLeaf Bistro/b01. Rating is the satisfaction observation. Mean CSAT is a
score out of five; satisfied percentage counts ratings >=4 separately. The FAQ
4.5 target and below-4.0 review threshold apply to the mean. Synthetic sentiment,
themes and complaint_themes are declared ground-truth annotations. The system
has not demonstrated classification accuracy on arbitrary real feedback.

Full data is included and remains Git-ignored. SHA256:
aa960ec95a9e2c87badc4c1c0a0d17ee8a7ea620407a04610f31b55b48783e36
It was regenerated during handoff preparation and matched the recorded evaluation.

## Historical verified results

Previous Linux/Python 3.12 run: 29 pytest tests passed, including actual embedding
retrieval. Three demo evaluations passed 33 checks. FAQ is 500 words; fine-tuning
proposal is 424 words and appears in README. No training job was performed.
The current handoff did not rerun those tests; rerun on the user's machine.

Expected deterministic data results:
- June count 53,000; mean rating 3.3624150943396227; satisfied 45.820754716981135%.
- June top complaints: wait_time 6,878; food_quality 4,713; value 3,292.
- May count 47,000; mean rating 3.642659574468085.
- Wait complaints May=3,056, June=6,878; delta=3,822; relative change=125.06544502617801%;
  prevalence delta=6.4752308309915705 percentage points.
- CSAT action: operations root-cause review, since June mean is below 4.0.
- Expected FAQ evidence: complaints faq-03, waiting faq-02, CSAT faq-04.

Previous independent review fixes covered unsupported demo scope, undefined empty
prevalence, missing comparison statistics in summaries, evaluation scope checks,
and stale cached vectors after another instance reingests. Do not regress them.

## Remaining work in execution order

1. Inspect Git status and preserve local user changes. This package contains .git
   and prior commits; no remote is configured. Use the current branch or an
   isolated continuation branch. Do not reinitialize or overwrite another repo.
2. Create a fresh Windows virtual environment using START_HERE.md. Install CPU
   PyTorch first, then requirements sequentially. Prior overlapping installers
   caused inconsistent dependencies; never install into one environment concurrently.
3. Validate the included dataset, build the real embedding index, run pytest and
   the demo. Missing model downloads are blockers, not permission to fake vectors.
4. Configure a tool-capable OpenAI-compatible LLM. Groq/gpt-oss-20b was suggested,
   but no hosted provider or local generative model has been verified. Confirm
   availability and costs. Ask the user to configure the key locally; do not print
   env values, request headers or provider bodies that may contain secrets.
5. Run one --provider llm question. Trace real plan generation, task validation,
   routing, tool arguments/results, retrieval and synthesis. Inspect actual
   failures; add regression tests and fix their causes.
6. Run the three canonical questions and write docs/live/evaluation.json plus
   docs/live/rag_evaluation.md. Use the same basename evaluation.json because the
   generated Markdown currently refers to that filename. Preserve demo artifacts.
7. Check numerical facts, requested date/business scopes, valid dependencies,
   citations, policy interpretation, provider/model identity and truthful mode labels.
   Add at least one paraphrase and an unsupported/out-of-scope question where useful.
8. Update README, requirements matrix, verification report and live retrieval
   observations to reflect execution, including limitations and any failures.
9. Run the full tests, dependency check, secret/identity audit and source review.
   Commit meaningful changes with Nachiket's identity; retain attribution.
10. Create/use the intended GitHub repo if the local GitHub/gh connection allows it.
    Do not overwrite a nonempty unrelated repository or force-push. User previously
    authorized publication of this assessment. If creation permission is missing,
    ask for an empty user-owned repository URL and finish everything else.
11. Push, clone the published repo into a new directory, create a new venv, regenerate
    data, ingest, run tests and live evaluation using only documented instructions.
    This clean checkout should not rely on files excluded from Git. Report its
    result separately from the original environment's results.
12. Deliver repo URL, final commit, real test/evaluation results and remaining
    limitations. Do not mark full integration complete before live evidence exists.

## Known areas to examine during live integration

- JSON-object mode guarantees neither Pydantic validity nor semantic correctness.
  Plan parsing currently has no repair/retry loop. Add bounded retries only where
  observed failures justify them, and retain failed-run evidence safely.
- Provider failures currently conceal HTTP status details. Improve safe diagnostics
  for 401/403, 429 and request errors without exposing secrets. Respect retry-after
  and use bounded handling if rate limits occur; do not enable paid billing silently.
- Evaluator currently expects one exact invocation order and data-task ordering.
  An LLM can produce a semantically valid alternative. Validate dependencies,
  required specialists, periods and results rather than blindly accepting or
  rejecting task-list order. Do not weaken required correctness checks.
- Some evaluation paths index expected results before checking malformed/missing
  tasks. Fail with a clear evaluation result rather than an accidental KeyError or
  IndexError. Ensure failed runs retain a useful trace; current evaluate saves
  only after all three questions finish.
- A data task computes exact results but provider function-call compatibility
  (schema refs, nullable fields, forced tool choice) is still unverified.
- Current final recommendation reads fixed 4.5/4.0 thresholds when the retrieved
  CSAT section is recognized. This matches the supplied FAQ, but do not claim a
  general policy extraction system. Preserve evidence or improve that logic if
  the FAQ is made configurable beyond the assessment fixture.
- .env.example documents settings; .env is not loaded automatically. A VS Code
  integrated terminal's exported variables may not reach Codex's separate shell.
  If adding dotenv support, keep it explicit, test configuration precedence and
  ensure .env remains untracked. Never read back or echo the user's key.

## Reference and attribution rules

All reference source was inspected; application code was independently written.
No license file was found at the four application snapshots. Do not copy their
source without establishing permission. Keep names/URLs in the attribution review;
active application identity must remain MiniSense/Nachiket. Preserve required
notices if any new material is reused.

References:
- https://github.com/mahfuz-raihan/agentic-rag-system
- https://github.com/ahmad2b/customer-feedback-analysis-ai-agent
- https://github.com/siddiquafathima/feedback-insights-pipeline-agent
- https://github.com/ro-anderson/multi-agent-rag-customer-support
- https://github.com/DietrichGebert/ponytail

Ponytail was used as simplicity/review guidance, not installed as a runtime or
persistent skill. Apply its small-complete-solution principle while preserving
validation and testing. The application uses conventional independent Python.

## Canonical commands

From repo root, using the venv interpreter:

```powershell
& $py -m minisense validate
& $py -m minisense ingest
& $py -m pytest -q
& $py -m pip check
& $py -m minisense --provider llm ask "What are the top three customer complaints in June 2026?" --json
& $py -m minisense --provider llm evaluate --output docs/live/evaluation.json
```

Global options precede subcommands. The remaining canonical questions are defined
in minisense/cli.py QUESTIONS. Keep generated data, index caches, .env and virtual
environments out of Git. No fine-tuning run, UI or deployment is needed to finish
mandatory assessment scope.
