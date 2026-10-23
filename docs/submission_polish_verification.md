# Submission completion evidence — 23 October 2026

This supplements the original agent and clean-install evidence. The existing
48-test/58-live-check reports remain historical execution records; no new live API
requests were necessary for this work, and the key pasted into chat was not used.

## Changes and checks

- Requirements matrix now points to the live planner, tool, synthesis and
  three-question evidence rather than historical demo-only rows. The README's
  primary evaluation links now open the actual live report.
- Retrieval observations now identify the required policy's actual rank and score,
  adjacent sections, empty queries and a question-specific limitation. Original
  live and clean-install JSON records were compared after excluding only the
  observation field: model requests, Python calls, answers, timestamps and all
  correctness checks are unchanged. Their Markdown reports were re-rendered.
- Historical docs/evaluation.json and docs/rag_evaluation.md are preserved
  byte-for-byte; failed-run artifacts also remain unchanged.
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

## Commands executed

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

## Published-checkout verification

Source revision a9bc0e63e6d0370aec0baa8e155e16c4eb35db58 was pulled from the
public repository into the independent minisense-clean-checkout workspace.
Its existing separate environment passed **55 tests**, including real CPU encoder
training and checkpoint prediction, in 17.69 seconds. pip check found no broken
requirements and tracked Git status remained clean. Original-workspace suite:
55 passed in 16.82 seconds. Exact logs are in finetuning/suite_original.txt and
finetuning/suite_published_checkout.txt.

The actual agent CLI was also run in demo mode with real embeddings and the new
report generator: all three questions passed 58 checks. No new live API call was
made; existing 58-check live evidence is preserved with improved commentary.
A fresh read-only code reviewer inspected connected source, fixtures, tests,
reports and documentation and found no must-fix issues. Secret/artifact audits
passed; no model weights, environments, raw generated data or secrets were staged.
The public implementation branch contains the additions and incremental history.
