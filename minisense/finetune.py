"""Optional CPU encoder fine-tuning baseline, isolated from the survey agent."""

import argparse
import hashlib
import json
import math
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


def validate_splits(train, validation, test, calibration=None):
    splits = [train, validation, test]
    if calibration is not None:
        splits.append(calibration)
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


def confidence_summary(logits, truth, policy):
    import torch
    values = torch.as_tensor(logits, dtype=torch.float32)
    if values.ndim != 2 or values.shape != (len(truth), len(LABELS)) or not len(truth) or not torch.isfinite(values).all():
        raise ValueError("Require finite N-by-eight logits matching nonempty labels")
    if any(type(v) is not int or not 0 <= v < len(LABELS) for v in truth):
        raise ValueError("Invalid calibration label IDs")
    probabilities = torch.softmax(values / policy["temperature"], dim=-1)
    confidence, guesses = probabilities.max(dim=-1)
    accepted = confidence >= policy["threshold"]
    count = int(accepted.sum())
    correct = guesses == torch.tensor(truth)
    return {"accepted": count, "abstained": len(truth) - count, "coverage": count / len(truth),
            "accepted_accuracy": int(correct[accepted].sum()) / count if count else None,
            "mean_confidence": float(confidence.mean())}


def fit_confidence_policy(logits, truth):
    import torch
    values = torch.as_tensor(logits, dtype=torch.float32)
    confidence_summary(values, truth, {"temperature": 1.0, "threshold": 0.8})
    temperatures = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0)
    temperature = min(temperatures, key=lambda t: float(torch.nn.functional.cross_entropy(values / t, torch.tensor(truth))))
    policy = {"temperature": temperature, "threshold": 1.01, "calibrated": True,
              "source": "separate calibration split", "target_accepted_accuracy": 0.95}
    for threshold in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        candidate = {**policy, "threshold": threshold}
        stats = confidence_summary(values, truth, candidate)
        if stats["coverage"] >= 0.8 and (stats["accepted_accuracy"] or 0) >= 0.95:
            return candidate
    # No reliable threshold: do not turn a weak classifier into confident predictions.
    return policy


def assessment_gates(metrics):
    return {"macro_f1": metrics["macro_f1"] >= 0.90,
            "negative_recall": all(metrics["per_class"][i]["recall"] >= 0.95 for i in (1, 2, 4, 5, 6)),
            "sufficient_class_support": len(metrics["per_class"]) == 8 and all(c["support"] >= 50 for c in metrics["per_class"]),
            "coverage": metrics["selective"]["coverage"] >= 0.80,
            "selective_accuracy": (metrics["selective"]["accepted_accuracy"] or 0) >= 0.95}


def train_model(train_path, validation_path, test_path, output, epochs=1, *,
                batch_size=4, learning_rate=2e-5, calibration_path=None, synthetic=False):
    if not 1 <= epochs <= 100:
        raise ValueError("Epochs must be between 1 and 100")
    if not 1 <= batch_size <= 128 or not math.isfinite(learning_rate) or not 0 < learning_rate <= 0.01:
        raise ValueError("Require batch size 1..128 and a finite positive learning rate <=.01")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be absent or empty; checkpoints are never overwritten")
    train, validation, test = [load_rows(p) for p in (train_path, validation_path, test_path)]
    calibration = load_rows(calibration_path) if calibration_path is not None else None
    validate_splits(train, validation, test, calibration)

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
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    steps, total_loss, history, stale = 0, 0.0, [], 0
    best_score, best_weights, best_epoch = None, None, None

    def infer(rows):
        logits = []
        model.eval()
        with torch.no_grad():
            for start in range(0, len(rows), batch_size):
                batch = tokenizer([r["text"] for r in rows[start:start + batch_size]], padding=True,
                                  truncation=True, max_length=128, return_tensors="pt")
                logits.append(model(**batch).logits)
        values = torch.cat(logits)
        truth = [LABELS.index(r["label"]) for r in rows]
        return values, truth

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss, epoch_steps = 0.0, 0
        for indices in torch.randperm(len(train)).split(batch_size):
            optimizer.zero_grad(set_to_none=True)
            loss = model(**{key: value[indices] for key, value in encoded.items()}, labels=labels[indices]).loss
            if not torch.isfinite(loss):
                raise ValueError("Non-finite training loss; no successful checkpoint claimed")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
            epoch_loss += loss.item()
            epoch_steps += 1
            steps += 1
        validation_logits, validation_truth = infer(validation)
        metrics = classification_metrics(validation_truth, validation_logits.argmax(dim=-1).tolist())
        validation_loss = float(torch.nn.functional.cross_entropy(validation_logits, torch.tensor(validation_truth)))
        entry = {"epoch": epoch, "train_loss": epoch_loss / epoch_steps,
                 "validation_macro_f1": metrics["macro_f1"], "validation_loss": validation_loss}
        history.append(entry)
        print(json.dumps(entry), flush=True)
        score = (metrics["macro_f1"], -validation_loss)
        if best_score is None or score > best_score:
            best_score, best_epoch = score, epoch
            best_weights = {name: value.detach().clone() for name, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        if stale >= 2:
            break
    model.load_state_dict(best_weights)
    encoder_changed = not torch.equal(initial, probe.detach())
    if not encoder_changed:
        raise RuntimeError("Encoder parameters did not change")
    model.eval()

    policy = {"temperature": 1.0, "threshold": 0.8, "calibrated": False, "source": "conservative uncalibrated default"}
    if calibration is not None:
        calibration_logits, calibration_truth = infer(calibration)
        policy = fit_confidence_policy(calibration_logits, calibration_truth)

    def evaluate(rows):
        values, truth = infer(rows)
        metrics = classification_metrics(truth, values.argmax(dim=-1).tolist())
        metrics["selective"] = confidence_summary(values, truth, policy)
        return metrics

    report = {"purpose": "CPU classifier assessment; synthetic or smoke data cannot establish production quality",
              "model": MODEL, "revision": REVISION, "method": "full encoder fine-tuning plus classification head",
              "device": "cpu", "seed": 42, "epochs_requested": epochs, "epochs": len(history), "batch_size": batch_size, "learning_rate": learning_rate,
              "max_length": 128, "optimizer_steps": steps, "mean_train_loss": total_loss / steps,
              "encoder_weights_changed": encoder_changed, "deployment_ready": False,
              "best_epoch": best_epoch, "checkpoint_selection": "validation macro-F1, then validation loss; never test metrics",
              "history": history, "confidence_policy": policy, "data_provenance": "synthetic" if synthetic else "unverified",
              "split_counts": dict(train=len(train), validation=len(validation), test=len(test)),
              "input_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                               for name, path in zip(("train", "validation", "test"), (train_path, validation_path, test_path))},
              "validation": evaluate(validation), "test": evaluate(test)}
    if calibration is not None:
        report["split_counts"]["calibration"] = len(calibration)
        report["input_sha256"]["calibration"] = hashlib.sha256(Path(calibration_path).read_bytes()).hexdigest()
    report["assessment_gates"] = assessment_gates(report["test"])
    report["assessment_ready"] = synthetic and all(report["assessment_gates"].values())
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)
    (output / "confidence_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    (output / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def predict(checkpoint, text):
    from .classifier_runtime import ClassifierRuntime, validate_text
    text = validate_text(text)
    return ClassifierRuntime(checkpoint).predict(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    training = commands.add_parser("train")
    for option in ("train", "validation", "test", "output"):
        training.add_argument(f"--{option}", type=Path, required=True)
    training.add_argument("--epochs", type=int, default=1)
    training.add_argument("--batch-size", type=int, default=4)
    training.add_argument("--learning-rate", type=float, default=2e-5)
    training.add_argument("--calibration", type=Path)
    training.add_argument("--synthetic", action="store_true", help="Mark data as synthetic; never authorizes production deployment")
    inference = commands.add_parser("predict")
    inference.add_argument("--checkpoint", type=Path, required=True)
    inference.add_argument("--text", required=True)
    args = parser.parse_args()
    if args.command == "train":
        report = train_model(args.train, args.validation, args.test, args.output, args.epochs,
                             batch_size=args.batch_size, learning_rate=args.learning_rate,
                             calibration_path=args.calibration, synthetic=args.synthetic)
        print(json.dumps({"optimizer_steps": report["optimizer_steps"], "encoder_weights_changed": report["encoder_weights_changed"],
                          "test_macro_f1": report["test"]["macro_f1"], "assessment_ready": report["assessment_ready"], "deployment_ready": False}))
    else:
        print(json.dumps(predict(str(args.checkpoint), args.text)))


if __name__ == "__main__":
    main()
