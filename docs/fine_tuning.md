# Fine tuning design

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
approved budget; Qwen adapter training is not executed.

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
