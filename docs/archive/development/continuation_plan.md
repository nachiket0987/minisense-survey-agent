# Windows continuation plan

Authority: Assignment.docx (all paragraphs and table cells read), CODEX_HANDOFF.md,
and the user's continuation request. Continue on the existing `implementation`
branch in the delivered isolated project; preserve demo artifacts and history.

- [x] Environment: workspace Python 3.12, sequential CPU PyTorch and requirements
  installation, validate supplied dataset and independently regenerate to compare
  hashes, build/reuse actual embedding index, run all tests and pip check.
- [x] Live provider: use the existing GROQ_API_KEY only in process memory, mapped
  explicitly to MINISENSE_API_KEY; user confirmed free-tier use. Confirm model
  through the API, run a canonical question before changing provider behavior.
  Add failing regression tests for observed issues before focused fixes.
- [x] Evaluation: reproduce ordering and missing-task defects in
  tests/test_evaluation.py; accept equivalent valid DAG order, retain independent
  scope/numeric checks, and persist partial failures without secret-bearing text.
  Capture actual model requests and execution, not just Python output.
- [x] Synthesis: assess existing constrained evidence renderer against assignment;
  retain exact facts and qualifiers. Change only if execution exposes a gap; label
  its actual role accurately in reports rather than implying free prose generation.
- [x] Review/docs: complete three live questions plus paraphrase/scope probes;
  update README, coverage and verification with Windows evidence, safe diagnostics,
  actual Ponytail use, limits, and precise reproducible commands. Keep fine-tuning
  design within 300–500 words. Review connected callers and secret hygiene.
- [x] Delivery: incremental commits; publish to intended empty repository if
  authenticated access becomes available; clone separately, create a fresh venv,
  follow README and repeat generation, ingestion, tests, CLI and live evaluation.

Review focus: equivalent task orders; missing outputs; failed provider calls;
incorrect date/business filters; unsupported recommendations. Each changed risky
behavior receives a regression test run red before the fix and green afterwards.

Ponytail: read current upstream SKILL.md, ponytail-review/SKILL.md, INSTALL.md and
MIT license. Apply its documented manual guidance here. Plugin setup requires
global marketplace/hook trust and a new thread, so it is not installed in this
ongoing workspace-scoped session. No upstream code or skill files redistributed.

Completed: published to the user-approved nachiket0987 repository. Separate GitHub clone regenerated data, built real embeddings, passed 48 tests/pip check, started CLI, and passed all three live questions/58 checks. See docs/clean-install.
