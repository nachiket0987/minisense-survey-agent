"""Optional CPU encoder fine-tuning baseline, isolated from the survey agent."""

import argparse
import hashlib
import json
from pathlib import Path

from pydantic import Field, field_validator
from .contracts import Contract

LABELS = (
    "Positive-Food", "Negative-Food", "Negative-Wait", "Positive-Staff",
    "Negative-Staff", "Negative-Order", "Negative-Value", "Neutral-Other",
)
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class LabeledText(Contract):
    text: str = Field(min_length=1)
    label: str
    group: str = Field(min_length=1)

    @field_validator("text", "group")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Text and group must be nonblank")
        return value.strip()

    @field_validator("label")
    @classmethod
    def known_label(cls, value):
        if value not in LABELS:
            raise ValueError("Unknown classification label")
        return value


def load_rows(path):
    rows = [LabeledText.model_validate_json(line).model_dump()
            for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("A split must contain labeled examples")
    return rows


def validate_splits(train, validation, test):
    splits = [train, validation, test]
    if any(not rows for rows in splits):
        raise ValueError("All three splits must be nonempty")
    if {r["label"] for r in train} != set(LABELS):
        raise ValueError("Training requires all eight labels")
    groups, texts = set(), set()
    for rows in splits:
        current_groups = {r["group"] for r in rows}
        current_texts = {" ".join(r["text"].casefold().split()) for r in rows}
        if groups & current_groups or texts & current_texts:
            raise ValueError("Cross-split group or normalized-text leakage")
        groups |= current_groups
        texts |= current_texts


def classification_metrics(truth, predicted):
    if not truth or len(truth) != len(predicted) or any(
        type(v) is not int or not 0 <= v < len(LABELS) for v in truth + predicted
    ):
        raise ValueError("Require equally sized nonempty integer label IDs in range 0..7")
    matrix = [[0] * len(LABELS) for _ in LABELS]
    for actual, guess in zip(truth, predicted):
        matrix[actual][guess] += 1
    per_class = []
    for i, label in enumerate(LABELS):
        tp = matrix[i][i]
        support = sum(matrix[i])
        guesses = sum(row[i] for row in matrix)
        precision = tp / guesses if guesses else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append(dict(label=label, support=support, precision=precision, recall=recall, f1=f1))
    return {"accuracy": sum(matrix[i][i] for i in range(len(LABELS))) / len(truth),
            "macro_f1": sum(row["f1"] for row in per_class) / len(LABELS),
            "per_class": per_class, "confusion_matrix": matrix}


def train_model(train_path, validation_path, test_path, output, epochs=1):
    if not 1 <= epochs <= 100:
        raise ValueError("Epochs must be between 1 and 100")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be absent or empty; checkpoints are never overwritten")
    train, validation, test = [load_rows(p) for p in (train_path, validation_path, test_path)]
    validate_splits(train, validation, test)

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed

    set_seed(42)
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, revision=REVISION, num_labels=len(LABELS),
        id2label=dict(enumerate(LABELS)), label2id={label: i for i, label in enumerate(LABELS)},
    ).to("cpu")
    # A small encoder matrix verifies that training updates the base, not just its head.
    probe = next(p for p in model.base_model.parameters() if p.ndim == 2 and p.numel() < 1_000_000)
    initial = probe.detach().clone()
    encoded = tokenizer([r["text"] for r in train], padding=True, truncation=True,
                        max_length=128, return_tensors="pt")
    labels = torch.tensor([LABELS.index(r["label"]) for r in train])
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    steps, total_loss = 0, 0.0
    model.train()
    for _ in range(epochs):
        for indices in torch.randperm(len(train)).split(4):
            optimizer.zero_grad(set_to_none=True)
            loss = model(**{key: value[indices] for key, value in encoded.items()}, labels=labels[indices]).loss
            if not torch.isfinite(loss):
                raise ValueError("Non-finite training loss; no successful checkpoint claimed")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
            steps += 1
    encoder_changed = not torch.equal(initial, probe.detach())
    if not encoder_changed:
        raise RuntimeError("Encoder parameters did not change")
    model.eval()

    def evaluate(rows):
        guesses = []
        with torch.no_grad():
            for start in range(0, len(rows), 4):
                batch = tokenizer([r["text"] for r in rows[start:start + 4]], padding=True,
                                  truncation=True, max_length=128, return_tensors="pt")
                guesses.extend(model(**batch).logits.argmax(dim=-1).tolist())
        return classification_metrics([LABELS.index(r["label"]) for r in rows], guesses)

    report = {"purpose": "CPU encoder baseline; smoke fixtures do not establish production quality",
              "model": MODEL, "revision": REVISION, "method": "full encoder fine-tuning plus classification head",
              "device": "cpu", "seed": 42, "epochs": epochs, "batch_size": 4, "learning_rate": 2e-5,
              "max_length": 128, "optimizer_steps": steps, "mean_train_loss": total_loss / steps,
              "encoder_weights_changed": encoder_changed, "deployment_ready": False,
              "split_counts": dict(train=len(train), validation=len(validation), test=len(test)),
              "input_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                               for name, path in zip(("train", "validation", "test"), (train_path, validation_path, test_path))},
              "validation": evaluate(validation), "test": evaluate(test)}
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)
    (output / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def predict(checkpoint, text):
    if not text.strip():
        raise ValueError("Prediction text must be nonblank")
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True).to("cpu").eval()
    if [model.config.id2label[i] for i in range(len(LABELS))] != list(LABELS):
        raise ValueError("Checkpoint does not use the MiniSense eight-label taxonomy")
    with torch.no_grad():
        logits = model(**tokenizer(text, return_tensors="pt", truncation=True, max_length=128)).logits
    return {"label": LABELS[logits.argmax(dim=-1).item()], "production_validated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    training = commands.add_parser("train")
    for option in ("train", "validation", "test", "output"):
        training.add_argument(f"--{option}", type=Path, required=True)
    training.add_argument("--epochs", type=int, default=1)
    inference = commands.add_parser("predict")
    inference.add_argument("--checkpoint", type=Path, required=True)
    inference.add_argument("--text", required=True)
    args = parser.parse_args()
    if args.command == "train":
        report = train_model(args.train, args.validation, args.test, args.output, args.epochs)
        print(json.dumps({"optimizer_steps": report["optimizer_steps"], "encoder_weights_changed": report["encoder_weights_changed"],
                          "test_macro_f1": report["test"]["macro_f1"], "deployment_ready": False}))
    else:
        print(json.dumps(predict(str(args.checkpoint), args.text)))


if __name__ == "__main__":
    main()
