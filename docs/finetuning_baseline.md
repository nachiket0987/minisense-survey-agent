# Executable CPU fine-tuning baseline

This optional bonus fully fine-tunes the MiniLM encoder and a new eight-label
classification head using the existing PyTorch/Transformers dependencies. It is
the smaller encoder baseline discussed in the required README proposal, not an
implementation or training run of that proposal's Qwen/LoRA adapter. It remains
separate from agent inference and does not change survey annotations or retrieval.

The pretrained model is sentence-transformers/all-MiniLM-L6-v2, pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Its upstream model card declares
Apache-2.0: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2.
Downloaded and trained weights remain local and retain upstream licensing.
No third-party training script was copied. Implementation follows the installed
Transformers sequence-classification interface and PyTorch optimization API.

## Data contract

Supply three UTF-8 JSONL files, one object per line:

```json
{"text":"The queue moved too slowly.","label":"Negative-Wait","group":"conversation-001"}
```

Accepted labels, in model ID order: Positive-Food, Negative-Food, Negative-Wait,
Positive-Staff, Negative-Staff, Negative-Order, Negative-Value, Neutral-Other.
Labels are mutually exclusive. A curated mixed-feedback example should receive
the most actionable negative label using a documented precedence rule. Abstain
for ambiguous or uncovered categories rather than silently relabeling them neutral.

The example files contain **handwritten artificial smoke fixtures**, not a
human-reviewed production corpus: 16 train, 8 validation and 8 test rows. They
verify mechanics only. All eight labels must appear in training. Cross-split
group overlap and normalized exact-text overlap are rejected. For real data,
assign conversation/business groups and chronological holdouts before creating
these files; fuzzy duplicates, privacy review and temporal leakage need separate
curation. This script does not claim to detect those automatically.

## Run and inspect

From the repo root after normal dependency installation:

```powershell
.\.venv\Scripts\python.exe -m minisense.finetune train --train examples/finetune/train.jsonl --validation examples/finetune/validation.jsonl --test examples/finetune/test.jsonl --output .cache/finetune-smoke --epochs 1
.\.venv\Scripts\python.exe -m minisense.finetune predict --checkpoint .cache/finetune-smoke --text "The staff were friendly and helpful."
```

An existing nonempty output directory is refused. Use a new output path for a
repeat experiment. The pinned public model may download on first use; no API key,
paid inference, GPU rental or new dependency is required. Runs use CPU, seed 42,
two CPU threads, batch size 4, AdamW at 2e-5 and maximum sequence length 128.
Longer inputs are truncated. The classification head starts newly initialized;
the corresponding Transformers warning is expected.

The output contains model.safetensors, tokenizer/config files and
training_report.json. It records data hashes, revision, hyperparameters, optimizer
steps, an actual encoder-weight-change check, and separate validation/test
accuracy, eight-class macro-F1, per-class precision/recall and confusion matrices.
The held-out test split is evaluated after training; no hyperparameter selection
uses it. This minimal baseline saves the final checkpoint; production jobs need
resumable checkpoints, early stopping and validation-only model selection.

## Actual smoke result and serving boundary

The Windows CPU run completed four optimizer steps and changed encoder weights.
Validation accuracy was 0.125, macro-F1 0.02778; test accuracy was 0.125,
macro-F1 0.03571. A checkpoint-reload prediction on a positive staff sentence
returned Negative-Value, demonstrating that this toy run is **not usable for
production**. `deployment_ready` and `production_validated` are explicitly false.
Metrics are recorded at finetuning/smoke_training_report.json.

The smoke proves that pretrained encoder loading, gradient updates, evaluation,
serialization and standalone inference work. It does not demonstrate learning
quality, release readiness, LoRA/QLoRA, frontier-model replacement, latency at
scale or the quality of a real eight-label corpus. Keep the classifier behind its
own command/process. A reviewed model could later expose the same label schema
through an isolated service route with shadow/canary rollout; no serving service
or production model is enabled here.
