# Execution and review evidence

## Final submission audit

On 2026-10-23, the final original-workspace run of
`.venv/Scripts/python.exe -m pytest -q` passed **61 tests in 16.49 seconds**.
`.venv/Scripts/python.exe -m pip check` reported **No broken requirements found**.
This finalization changes documentation only. The recorded three-question live
evaluation and independent checkout evidence below remain the execution records;
no additional hosted LLM requests or full classifier retraining were performed.

## Latest classifier assessment

The user authorized synthetic data for this improvement. Root cause of the poor
smoke model: 16 training examples and four updates for a new eight-class head.
The fixed larger experiment uses 1,600/512/512/800 train/validation/calibration/test
examples and disjoint core-clause families. Validation alone chooses checkpoints;
calibration alone chooses confidence policy; test predictions are computed only
after selection. Test accuracy **0.9675**, macro-F1 **0.9669**, minimum negative-class recall **1.0000**. Accepted-prediction coverage **1.0000**, accepted accuracy **0.9675**. Assessment gates passed.
See [classifier details](finetuning_baseline.md) and
[actual report](finetuning/assessment_training_report.json).

The full current suite passed **61 tests**. A fresh read-only reviewer found no
must-fix issues in the split, selection, calibration and gate logic. A boundary
regression also prevents float32 rounding from rejecting exactly 95% accepted
accuracy. No paid service or API key was used. Original smoke, demo, live agent
and clean-install evidence remains unchanged. Production flags remain false;
human-reviewed real-data validation and operational approval are still required.

Positive-Food recall was 0.74; all five negative-class recalls were 1.0. The
confidence rule abstained on none of the 800 test examples, so it did not catch
the Positive-Food errors. These limits are explicit in the classifier report;
the test set was not altered or used to tune another run.


The independent published checkout at source revision c78be04 passed **61 tests**
in 17.67 seconds and pip check found no broken requirements. Regenerating its
four synthetic splits reproduced all counts, family counts and input SHA256
hashes exactly. Its smoke training integration test ran; the full 800-step
assessment experiment was not repeated there. The earlier original-workspace
suite passed in 24.63 seconds. Exact output is consolidated in
[test_results.txt](finetuning/test_results.txt). Model weights and generated raw
classifier JSONL files remain local and ignored. Neither the classifier work nor
its reproduction used any hosted LLM API or the exposed credential.

## Earlier submission completion

This supplements the original agent and clean-install evidence. The existing
48-test/58-live-check reports remain historical execution records; no new live API
requests were necessary for this work, and the key pasted into chat was not used.

### Changes and checks

- Requirements matrix now points to the live planner, tool, synthesis and
  three-question evidence rather than historical demo-only rows. The README's
  primary evaluation links now open the actual live report.
- Retrieval observations now identify the required policy's actual rank and score,
  adjacent sections, empty queries and a question-specific limitation. Original
  live and clean-install JSON records were compared after excluding only the
  observation field: model requests, Python calls, answers, timestamps and all
  correctness checks are unchanged. Their Markdown reports were re-rendered.
- Historical docs/evaluation.json and docs/rag_evaluation.md are preserved
  byte-for-byte; failed-run artifacts retain their original bytes under archive/evaluations/.
- Optional CPU full encoder fine-tuning runs separately via minisense.finetune.
  The pretrained MiniLM revision is pinned; JSONL labels and nonblank fields are
  validated, all eight labels are required in training, and cross-split exact
  normalized-text/group leakage is rejected. Existing checkpoints are protected.
- A real CPU smoke run used 16 training, 8 validation and 8 test artificial rows,
  seed 42, one epoch, four optimizer steps. Encoder parameters changed and a
  safetensors checkpoint/tokenizer were saved and reloaded for standalone
  prediction. No GPU, paid service, API key or new dependency was needed.
- The resulting model is poor: validation macro-F1 0.02778, test macro-F1 0.03571;
  both accuracies are 0.125. A positive staff sentence was misclassified as
  Negative-Value. Reports explicitly set deployment_ready/production_validated
  false. This verifies machinery, not production performance or Qwen/LoRA training.
- Full Windows suite: **55 passed**, including original real retrieval plus real
  CPU training/checkpoint inference. Contract, leakage, metrics and retrieval
  commentary regressions were observed failing before their implementation.
- The required fine-tuning design remains **424 words**; the FAQ remains 500 words.
  The optional baseline is documented outside the required essay.

### Commands executed

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_finetune.py -q
.\.venv\Scripts\python.exe -m minisense.finetune train --train examples/finetune/train.jsonl --validation examples/finetune/validation.jsonl --test examples/finetune/test.jsonl --output .cache/finetune-smoke --epochs 1
.\.venv\Scripts\python.exe -m minisense.finetune predict --checkpoint .cache/finetune-smoke --text "The staff were friendly and helpful."
.\.venv\Scripts\python.exe -m pytest -q
```

The expected newly initialized classifier-head warning was emitted on first
pretrained-model loading. The temporary documentation-refresh script initially
could not import the repo when run from .cache; executing it with the repo on
Python's import path resolved that, before any artifact changes were made.

Key rotation cannot be verified or performed through the available project tools.
The account owner must revoke the exposed key and replace it locally. No claim
that this account action has been completed is made.

### Published-checkout verification

Source revision a9bc0e63e6d0370aec0baa8e155e16c4eb35db58 was pulled from the
public repository into the independent minisense-clean-checkout workspace.
Its existing separate environment passed **55 tests**, including real CPU encoder
training and checkpoint prediction, in 17.69 seconds. pip check found no broken
requirements and tracked Git status remained clean. Original-workspace suite:
55 passed in 16.82 seconds. Exact logs are in [finetuning/test_results.txt](finetuning/test_results.txt).

The actual agent CLI was also run in demo mode with real embeddings and the new
report generator: all three questions passed 58 checks. No new live API call was
made; existing 58-check live evidence is preserved with improved commentary.
A fresh read-only code reviewer inspected connected source, fixtures, tests,
reports and documentation and found no must-fix issues. Secret/artifact audits
passed; no model weights, environments, raw generated data or secrets were staged.
The public implementation branch contains the additions and incremental history.

## Windows continuation — 23 October 2026

The sections below this continuation retain historical Linux evidence. Current
Windows verification uses Python 3.12.11, CPU PyTorch 2.6.0+cpu, uv 0.7.12 and
the installed dependency snapshot in windows_environment.txt. No GPU was assumed;
`torch.cuda.is_available()` returned false. Python was installed under ignored
`.tools/python`; the virtual environment is ignored `.venv`.

Actual commands executed from the repository root (installations sequential):

```powershell
uv python install 3.12 --install-dir .tools/python
.\.tools\python\cpython-3.12.11-windows-x86_64-none\python.exe -m venv .venv
uv pip install --python .venv/Scripts/python.exe torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.\.venv\Scripts\python.exe -m minisense validate
.\.venv\Scripts\python.exe -m minisense ingest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m minisense --help
# Same-shell credentials were mapped in memory; never printed or persisted.
.\.venv\Scripts\python.exe -m minisense --provider llm ask "What are the top three customer complaints in June 2026?" --json
.\.venv\Scripts\python.exe -m minisense --provider llm evaluate --output docs/live/evaluation.json
```

Results: the 100,000-response dataset passed full validation. Independent
regeneration into `.cache/regenerated.json` matched SHA256
`aa960ec95a9e2c87badc4c1c0a0d17ee8a7ea620407a04610f31b55b48783e36`.
Actual all-MiniLM-L6-v2 ingestion built seven 384-dimensional vectors; repeating
ingestion returned `rebuilt: false`. All 29 original tests passed locally before
the continuation fixes. Final expanded suite: **48 passed**. `pip check`: no
broken requirements. Final live assessment: **3 questions, 58 checks passed**.
The separate paraphrase and unknown-business/exact-date probes also passed; see
live/probes.json. None of these live runs uses the deterministic demo planner.

Groq's authenticated model-list endpoint confirmed openai/gpt-oss-20b active. The
user explicitly confirmed free-tier use of the existing GROQ_API_KEY. Each command
mapped it to MINISENSE_API_KEY within that process; no terminal inheritance was
assumed. No dotenv loader, paid capacity or fine-tuning job was introduced.

Observed failures and focused fixes (regressions run failing before the fix):

- pip 26.2.2 and 25.0.1 both hit WinError 5 replacing SymPy RECORD metadata.
  Direct replacement succeeded; the preinstalled uv completed sequential installs.
  Host-installed package cache files were inaccessible to the sandbox account;
  verification ran with approved host execution. This is an agent sandbox detail,
  not a requirement for users to run Python as Administrator.
- Live planner returned invalid agent/operation pairs, nullable numeric defaults,
  omitted RAG, and confused target comparisons with period comparisons. Explicit
  task-role guidance plus at most three schema-validation attempts now preserve
  rejected requests without running invalid plans. Semantic correctness is still
  checked separately in evaluation; schema validity alone is insufficient.
- A real 429 exposed weak diagnostics and quota handling. Status-only errors and
  at most two retries for a numeric Retry-After <=60 seconds retain free-tier limits.
- Evaluator rejected alternative task ordering/additional context tasks, crashed
  on missing data, and discarded partial failures. It now checks DAG dependencies,
  required scope/cardinality/specialists, independent statistics, actual tool
  outputs and final policy grounding, and writes each question incrementally.
- Failure records shared a mutable provider buffer. Deep snapshots now retain the
  correct question's trace. Attempt-01's affected partial trace is explicitly
  marked unreliable in live/README.md.
- Live summary selection omitted one evidence item. Bounded validated feedback
  now permits correction; every fact must still appear once and recommendations
  remain allowlisted. Invalid selections never become successful demo answers.
- Fresh review found wrong top-three cardinality, misleading labels for partial
  date ranges, and an invalid HTTP-200 message envelope. Focused regressions now
  cover these cases. A read-only reviewer inspected source, callers, tests and
  requirements; its three concrete findings were fixed.

Synthesis decision: the assignment asks for a coherent narrative paragraph and
structured specialist output, not unrestricted generation. The current summary
meets that requirement by giving the LLM metrics and retrieved passages, validating
its evidence ordering/recommendation, and preserving exact facts and complete
policy qualifiers in Python. Its style is constrained and verbose; no claim of
free generative rewriting is made. Policy thresholds remain tied to the supplied
FAQ fixture, and synthetic annotations do not prove real-text classification.

Ponytail was used manually after reading current upstream implementation/review
skills, README, INSTALL.md and MIT license. Its documented Codex plugin setup
requires marketplace changes, lifecycle-hook trust and a new thread; this session
kept configuration workspace-scoped and applied the documented smallest-complete-
change and connected-code-review guidance. No Ponytail code was redistributed.

Publication target was changed by explicit user instruction to
`nachiket0987/minisense-survey-agent`. With approved network access, gh is signed
in as nachiket0987; earlier sandbox-only auth checks falsely reported an invalid
token. The connected app remains psychochan. No repository belonging to another
account is overwritten. Recorded clean-checkout evidence follows.

## Published clean-checkout verification

Public repository: https://github.com/nachiket0987/minisense-survey-agent
Default branch: implementation. Tested source revision: `7cb3586974599283e1e75a7d904d4df2066f46a1`.
Cloned from GitHub into sibling minisense-clean-checkout; the clone initially
contained neither data/responses.json nor data/index. Installed Python 3.12.11
under that checkout's own .tools/python and created its own .venv. CPU PyTorch
and requirements were installed sequentially. Standard download caches were
reused; no original-workspace data, vector index, environment or scripts were used.

The first venv command reported an ensurepip failure. Running
`python -m ensurepip --upgrade --default-pip` confirmed pip 25.0.1 installed;
the README now documents this recovery. Generation, full validation, real
ingestion, CLI --help, demo ask and three-question demo evaluation all succeeded.
The dataset matched the same SHA256; the fresh index has shape (7, 384).
Final clean suite: **48 passed**; pip check: no broken requirements.

The first repeated live run exposed another evaluator false rejection: CSAT
with theme=satisfaction still computes the mean over every scoped response;
theme only projects the complaint breakdown. A regression was observed failing,
then fixed while retaining independent count/mean/rate/tool/policy checks.
That first run remains under archive/evaluations/clean-install/attempt-01. After pulling the fix,
all three live questions passed **58 checks** from the clean checkout. Exact
live traces, retrieved passages, answers and pytest output are in clean-install/.
The checkout's tracked Git status remained clean after execution because repeat
outputs use ignored .cache paths. See clean-install/verification.json.

Final audit checked the actual local key is absent from source and artifacts,
confirmed ignored secrets/environments/data/indexes, preserved historical demo
artifacts byte-for-byte, and counted FAQ=500 and fine-tuning proposal=424 words.
No paid service or training job was enabled. The one public-publication auto-review
rejection was resolved by the user's explicit approval of public visibility and
the reviewed synthetic statistics, FAQ excerpts and model/tool traces payload.

## Historical Linux execution

Executed on Linux, Python 3.12, 23 October 2026. Final commands use `.venv-clean`
because the initial environment was replaced after a dependency-install conflict.
The README uses the conventional `.venv` directory for a clean user installation.

## Commands executed

- Read all paragraphs and tables of the supplied DOCX with python-docx.
- Shallow-cloned all five supplied GitHub repositories and inspected source,
  dependency manifests, and available licenses; recorded snapshot SHAs.
- Created isolated environment; installed CPU PyTorch 2.6.0 and requirements.
- `python -m minisense generate`
- `python -m minisense validate`
- `python -m minisense ingest`
- `python -m minisense --help`
- `python -m minisense ask ... --json` (see final verification below)
- `python -m minisense evaluate`
- `python -m pytest -m "not integration" -q`
- `python -m pytest tests/test_retrieval.py -m integration -q`
- `python -m pytest -q`
- `python -m pip check`
- `python -m minisense --provider llm ask "CSAT in June 2026"`
- Git commits, diff whitespace check, tracked-source identity and secret scans.

## Results

Dataset: exactly 100,000 unique IDs, 47,000 May and 53,000 June responses,
all b01/GreenLeaf Bistro. Four sentiment classes; 65,458 unique feedback strings.
Full schema validation passed; hash and counts are in dataset_validation.json.
FAQ: exactly 500 whitespace-delimited words, seven Q/A sections. Ingestion used
the actual all-MiniLM-L6-v2 model and wrote seven 384-dimensional normalized
vectors. Repeat ingestion returned `rebuilt: false`.

Real-model integration test passed. Three assessment questions ran with real
embeddings, exact analytics and deterministic demo planning/synthesis. All 33
explicit evaluation checks passed, including expected periods/business, specialist
routing, independent complaint/mean calculations, comparison changes and relevant
FAQ section retrieval. They are not live generative-LLM integration results.

Final full suite: **29 passed**, with the real embedding integration test included.
`python -m pip check` reported no broken requirements; `compileall` and Git
whitespace checks passed. The final active-source scan checked 17 source/config
files and found no secret/contact matches or old developer branding.

## Failures observed and resolved

Initial test collection failed before retrieval/agent/CLI modules existed, then
passed after implementation. The earliest analytics test attempt could not run
because pytest installation had not finished; it is not presented as a red test.

An initial unconstrained ML install and overlapping downgrade attempts produced
mixed PyTorch files and Transformers/tokenizers incompatibilities. The concrete
errors included a missing SerializationFormat import and invalid tokenizers
metadata. A fresh environment, CPU PyTorch 2.6.0, sentence-transformers 3.4.1,
Transformers 4.48.3 and tokenizers 0.21 resolved them. Future installations should
follow the documented sequential commands, not concurrent dependency mutations.

A unit test encountered the host's SOCKS proxy without socksio; httpx[socks] now
includes the required transport support. Independent review reproduced six failing
scope/summary/empty-data cases and a stale-vector-cache bug. Regression tests were
written before the fixes and passed afterwards. Evaluation rendering initially
formatted an optional absent score as a float; it now displays `unavailable`.

## Independent review

A separate reviewer inspected source, contracts, tests and design. Fixed its
important findings: unsupported demo scopes, undefined empty prevalence,
missing rating/volume comparison statements, evaluator scope blindness, and
cached vectors paired with newly ingested metadata. Full FAQ answers retain
qualifying language. The reviewer did not rerun after fixes; regression tests and
the final full suite verify the changes. No claim of a second review is made.

## Identity and secret audit

The four reference application sources were not copied. Active application
configuration contains no original developer names, unrelated contact addresses,
or old branding. Reference URLs remain intentionally in README and reference_review.
No account email is embedded as an application contact. `.env`, environments,
generated survey JSON and vector caches are ignored. Git uses a GitHub noreply
identity. Package/model dependencies retain their upstream licenses.

## Explicit blockers and unverified behavior

No LLM endpoint/model credentials are configured. LLM mode exits with a clear
configuration error. Provider transport, plan validation and function-call guards
are unit-tested with labeled mocks; real LLM task planning, API function calling
and synthesis remain unverified. A tool-capable compatible endpoint is required
before calling the entire AI assessment integration complete. No training occurred.

The connected GitHub profile is psychochan. The connector exposes repository
reads and file/commit mutations, but no repository-creation operation; no target
MiniSense repository was found, and no authenticated Git CLI is configured.
No remote repository was created or overwritten. A local Git bundle and clean
source archive preserve the work for importing into an empty user-owned repo.
Windows instructions were written but runtime checks occurred on Linux only.
