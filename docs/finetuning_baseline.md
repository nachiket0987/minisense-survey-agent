# Trained CPU classifier for the assessment

The classifier now has an executed synthetic assessment experiment, beyond the
original four-step smoke test. It fully fine-tunes the pinned MiniLM encoder and
eight-label head on CPU using the existing dependencies. It remains separate from
survey analytics and FAQ retrieval. No paid service, API key or GPU rental is used.

The user explicitly chose synthetic data. These results demonstrate performance
on a generated benchmark, not production quality on real feedback. The Qwen/LoRA
approach in the 424-word README section remains a proposed alternative.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m minisense.classifier_data --output .cache/classifier-data
.\.venv\Scripts\python.exe -m minisense.finetune train --train .cache/classifier-data/train.jsonl --validation .cache/classifier-data/validation.jsonl --calibration .cache/classifier-data/calibration.jsonl --test .cache/classifier-data/test.jsonl --output .cache/classifier-assessment --epochs 8 --batch-size 16 --learning-rate 0.00005 --synthetic
.\.venv\Scripts\python.exe -m minisense.finetune predict --checkpoint .cache/classifier-assessment --text "The staff were friendly and helpful."
```

Existing nonempty output directories are refused; choose new paths when repeating
an experiment. The initial encoder is sentence-transformers/all-MiniLM-L6-v2,
revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The
[upstream model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
declares Apache-2.0. Trained/downloaded weights remain ignored and retain upstream
licensing. No third-party training script was copied.

## Data and leakage controls

There are 3,424 generated examples across eight balanced classes: 1,600 train,
512 validation, 512 calibration and 800 test. Entire clause-template families are
held out: 64 train, 24 validation, 24 calibration and 32 test families. Negation
and mixed positive/negative feedback are included. A single negative topic takes
precedence over a positive mention. Context wrappers are shared across splits;
core clauses are not. Examples within a template family are correlated variants,
so 800 test rows do not represent 800 independently authored customer experiences.

The generator is seeded, versioned in minisense/classifier_data.py and reproducible.
The report embeds split counts, family counts and SHA256 hashes. Group and
normalized exact-text overlap is rejected across every split. These checks do not
prove absence of semantic similarity or coverage of real-world language.

External UTF-8 JSONL inputs use this contract:

```json
{"text":"The queue moved too slowly.","label":"Negative-Wait","group":"conversation-001"}
```

Labels in ID order: Positive-Food, Negative-Food, Negative-Wait, Positive-Staff,
Negative-Staff, Negative-Order, Negative-Value, Neutral-Other. Training requires
all eight classes. Neutral-Other is neutral/factual feedback, not a fallback label
for arbitrary positive/negative topics. Uncovered or ambiguous taxonomy cases need
human review and additional evaluation data. For real corpora, curate privacy,
conversation/business groups, chronology and fuzzy duplicates before splitting.

## Training and confidence policy

The fixed experiment used seed 42, two CPU threads, AdamW at 5e-5, batch size 16,
max sequence length 128 and at most eight epochs. Checkpoint selection uses only
validation macro-F1, breaking ties with validation loss. Two non-improving epochs
stop training. The selected epoch was **6**, after
**8** executed epochs and **800** optimizer steps.
The encoder-weight-change check passed; the classification head starts initialized
from scratch, as shown by the expected Transformers warning.

A separate calibration split chooses a temperature from a fixed grid by log loss,
then the lowest confidence threshold reaching 95% accepted accuracy and 80%
coverage on that calibration split. If none qualifies, all predictions abstain.
The test split is evaluated once after checkpoint and confidence selection.
Defaults without a calibration split use an explicitly uncalibrated 0.8 threshold.
Inference returns label, candidate_label, confidence, abstained and review_required;
the final label is always null in the current shadow runtime. Confidence calibration
on synthetic data does not guarantee reliability or detect out-of-distribution
inputs on real feedback. The runtime rejects inputs exceeding the trained
128-token limit instead of silently truncating them.

## Actual held-out results

Test accuracy **0.9675**, macro-F1 **0.9669**, minimum negative-class recall **1.0000**. Accepted-prediction coverage **1.0000**, accepted accuracy **0.9675**.

Assessment gates **passed**. They require macro-F1 >=0.90, each negative
class recall >=0.95, at least 50 examples per test class, coverage >=0.80 and
accepted accuracy >=0.95. Full confusion matrices, per-class metrics, validation
history, calibration policy and hashes are in
[assessment_training_report.json](finetuning/assessment_training_report.json).
Test scores were not used to choose epochs, learning rate or thresholds.

The per-class results expose an important weakness: Positive-Food recall is
**0.74** (26 of 100 examples missed), while the other seven classes have recall
1.0. The confidence policy accepted all 800 test examples, including those errors;
its mean confidence of 0.9959 exceeds actual accuracy of 0.9675. Thus the review
mechanism does not reliably catch this held-out family's errors. The predefined
macro/negative-class gates passed, but they are not a guarantee for every class.
This result is disclosed without tuning against or replacing the test set.

The original 16/8/8 smoke run remains at
[smoke_training_report.json](finetuning/smoke_training_report.json): its macro-F1
was only 0.03571. That historical result is preserved rather than overwritten.

## Deployment boundary

### Shadow runtime hardening

`ClassifierRuntime` loads the local CPU checkpoint once per worker and reuses it.
It validates the eight-label taxonomy, confidence-policy numeric bounds, finite
logits, nonblank text, a 10,000-character cap and the trained 128-token boundary.
It makes no downloads or API calls and does not log input text. Callers must route
input errors to human review; they must not substitute a guessed final label.

Because the model is unvalidated and confidently wrong on challenge cases, every
result now has `label: null`, `review_required: true`, `abstained: true`,
`mode: shadow` and `reason: checkpoint_not_production_validated`.
`candidate_label`, `confidence` and `confidence_threshold_met` are diagnostic
suggestions only. There is no switch or checkpoint metadata flag that enables
automatic decisions. This intentionally changes the old CLI acceptance behavior.

```python
from minisense.classifier_runtime import ClassifierRuntime

runtime = ClassifierRuntime(".cache/classifier-assessment")
suggestion = runtime.predict("The staff were friendly.")
# Display candidate_label to a reviewer; label remains None.
```

The [shadow audit](finetuning/shadow_audit.json) ran the same frozen checkpoint:
13/16 original and 7/8 fresh assistant-labeled candidates correct. All 30 inputs,
including six unsupported or ambiguous probes, require review; zero automatic
decisions means zero automatic coverage, not perfect classifier accuracy.
Blank, oversized and over-128-token input probes were rejected. Sequential warm
median latency was 0.0072 seconds; startup was 6.17 seconds. These timings are
local diagnostics, not a concurrency or deployment SLA.
Reproduce with `.venv/Scripts/python.exe docs/finetuning/run_shadow_audit.py`.
The original readiness report remains unchanged; its older reproduction script
now writes `.cache/readiness-audit-current.json` to preserve historical evidence.

### Additional readiness audit (2026-10-23)

An offline frozen-checkpoint challenge audit correctly classified **13/16** new
in-scope examples (81.25%). All three incorrect predictions were accepted.
None of six out-of-scope, multilingual or ambiguous probes triggered abstention.
These assistant-authored cases are diagnostic synthetic examples, not independent
human annotations or representative customer data. They provide additional
evidence against production readiness; they do not replace the held-out benchmark.
No retraining or threshold tuning used these results.

Sequential local calls had median latency **0.0582 seconds** and maximum
**6.0354 seconds**, with model/tokenizer reloading per call and initial imports
included. This is not a serving throughput or concurrent-load measurement.
See the [full results](finetuning/readiness_audit.json) and
[reproduction script](finetuning/run_readiness_audit.py). Run the script from the
repository root using the existing environment and local checkpoint:

```powershell
.\.venv\Scripts\python.exe docs/finetuning/run_readiness_audit.py
```

Production validation cannot be completed with the available synthetic-only
data. The next required input is representative real feedback with independent
human-reviewed eight-label annotations and privacy/usage authorization. Its
untouched test set must assess every class, ambiguous/unsupported topics and
confidence failures before operational shadow testing and deployment approval.

The improved checkpoint is local at `.cache/classifier-assessment`. It is not
automatically enabled in the survey agent or published as model weights.
`assessment_ready` reports synthetic gate status; `deployment_ready` and
`production_validated` remain false. Real deployment still requires a representative
human-reviewed corpus, independent external test/challenge sets, taxonomy review,
uncertainty/OOD validation, latency/load measurements, operational sign-off and
shadow/canary rollout. The standalone CLI loads the checkpoint per process; a
long-running serving route should reuse the model. No such service is enabled.
