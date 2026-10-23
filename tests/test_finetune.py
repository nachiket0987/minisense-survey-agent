import json
import pytest


def write_rows(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return path


def test_label_contract_and_all_classes_required(tmp_path):
    from minisense.finetune import LABELS, load_rows, validate_splits
    rows = [{"text": f"example {i}", "label": label, "group": f"g{i}"}
            for i, label in enumerate(LABELS)]
    path = write_rows(tmp_path / "train.jsonl", rows)
    train = load_rows(path)
    with pytest.raises(ValueError, match="all eight"):
        validate_splits(train[:-1], [dict(rows[-1], text="validation", group="validation")],
                        [dict(rows[-1], text="test", group="test")])
    rows[0]["label"] = "unknown-label"
    with pytest.raises(ValueError):
        load_rows(write_rows(path, rows))


@pytest.mark.parametrize("field,value", [("text", "  EXAMPLE 0  "), ("group", "g0")])
def test_split_leakage_rejected(tmp_path, field, value):
    from minisense.finetune import LABELS, validate_splits
    train = [{"text": f"example {i}", "label": label, "group": f"g{i}"}
             for i, label in enumerate(LABELS)]
    valid = [{"text": "validation", "group": "validation", "label": LABELS[0]}]
    valid[0][field] = value
    test = [{"text": "test", "group": "test", "label": LABELS[1]}]
    with pytest.raises(ValueError, match="leakage"):
        validate_splits(train, valid, test)


def test_metrics_use_all_eight_classes_and_report_confusion():
    from minisense.finetune import classification_metrics
    metrics = classification_metrics([0, 1], [0, 0])
    assert metrics["accuracy"] == 0.5
    assert metrics["macro_f1"] == pytest.approx(1 / 12)
    assert metrics["confusion_matrix"][1][0] == 1
    assert metrics["per_class"][0]["precision"] == 0.5
    assert metrics["per_class"][1]["recall"] == 0
    with pytest.raises(ValueError):
        classification_metrics([], [])
    with pytest.raises(ValueError):
        classification_metrics([8], [0])


def test_existing_checkpoint_is_not_overwritten(tmp_path):
    from minisense.finetune import train_model
    marker = tmp_path / "keep.txt"
    marker.write_text("existing checkpoint")
    with pytest.raises(ValueError, match="never overwritten"):
        train_model("unused", "unused", "unused", tmp_path)
    assert marker.read_text() == "existing checkpoint"


def test_calibration_split_leakage_is_rejected():
    from minisense.finetune import LABELS, validate_splits
    train = [{"text": label, "label": label, "group": str(i)} for i, label in enumerate(LABELS)]
    valid = [{"text": "validation", "label": LABELS[0], "group": "v"}]
    test = [{"text": "held out", "label": LABELS[0], "group": "t"}]
    with pytest.raises(ValueError, match="leakage"):
        validate_splits(train, valid, test, [dict(test[0], text="calibration")])


def test_confidence_policy_abstains_when_calibration_is_unreliable():
    from minisense.finetune import fit_confidence_policy, confidence_summary
    logits = [[9.0] + [0.0] * 7, [9.0] + [0.0] * 7]
    policy = fit_confidence_policy(logits, [0, 1])
    stats = confidence_summary(logits, [0, 1], policy)
    assert stats["accepted"] == 0
    assert stats["accepted_accuracy"] is None
    assert stats["coverage"] == 0


def test_assessment_gates_require_support_recall_and_selective_quality():
    from minisense.finetune import assessment_gates
    metrics = {"macro_f1": 0.99, "per_class": [{"support": 100, "recall": 1.0} for _ in range(8)],
               "selective": {"coverage": 1.0, "accepted_accuracy": 0.99}}
    assert all(assessment_gates(metrics).values())
    metrics["per_class"][2]["recall"] = 0.94
    assert not assessment_gates(metrics)["negative_recall"]
    metrics["per_class"][2]["recall"] = 1.0
    metrics["per_class"][0]["support"] = 1
    assert not assessment_gates(metrics)["sufficient_class_support"]
    metrics["selective"]["accepted_accuracy"] = None
    assert not assessment_gates(metrics)["selective_accuracy"]


def test_confidence_accuracy_preserves_the_95_percent_gate_boundary():
    from minisense.finetune import confidence_summary
    stats = confidence_summary([[9.0] + [0.0] * 7] * 20, [0] * 19 + [1],
                               {"temperature": 1.0, "threshold": 0.5})
    assert stats["accepted_accuracy"] == 0.95


@pytest.mark.integration
def test_real_cpu_encoder_training_and_checkpoint_prediction(tmp_path):
    from minisense.finetune import LABELS, train_model, predict
    from pathlib import Path
    fixtures = Path("examples/finetune")
    report = train_model(fixtures / "train.jsonl", fixtures / "validation.jsonl",
                         fixtures / "test.jsonl", tmp_path)
    assert report["optimizer_steps"] == 4
    assert report["encoder_weights_changed"] is True
    assert report["split_counts"] == {"train": 16, "validation": 8, "test": 8}
    assert report["deployment_ready"] is False
    assert len(report["test"]["per_class"]) == 8
    assert (tmp_path / "model.safetensors").exists()
    output = predict(str(tmp_path), "The food tasted fresh.")
    assert output["candidate_label"] in LABELS
    assert output["label"] in (*LABELS, None)
    assert output["review_required"] == output["abstained"]
    assert output["production_validated"] is False
    assert output["label"] is None
    assert output["reason"] == "checkpoint_not_production_validated"
    from minisense.classifier_runtime import ClassifierRuntime
    runtime = ClassifierRuntime(tmp_path)
    model = runtime.model
    assert runtime.predict("The waiter was rude.")["review_required"]
    assert runtime.predict("Our meal was delicious.")["label"] is None
    assert runtime.model is model
    with pytest.raises(ValueError, match="128-token"):
        runtime.predict("food " * 150)


@pytest.mark.parametrize("text", ["", "   ", None, 42, "a" * 10001])
def test_runtime_rejects_invalid_input_before_loading_model(text):
    from minisense.classifier_runtime import validate_text
    from minisense.finetune import predict
    with pytest.raises(ValueError):
        validate_text(text)
    with pytest.raises(ValueError, match="Require nonblank"):
        predict("nonexistent-checkpoint-must-not-be-loaded", text)


@pytest.mark.parametrize("policy", [
    {}, {"temperature": 0, "threshold": 0.5},
    {"temperature": float("nan"), "threshold": 0.5},
    {"temperature": 1, "threshold": -1},
    {"temperature": 1, "threshold": float("inf")},
    {"temperature": True, "threshold": 0.5},
])
def test_runtime_rejects_unsafe_confidence_policy(policy):
    from minisense.classifier_runtime import validate_policy
    with pytest.raises(ValueError):
        validate_policy(policy)


def test_runtime_never_automatically_accepts_confident_synthetic_prediction():
    from minisense.classifier_runtime import review_decision
    result = review_decision("Positive-Food", 0.999999, 0.5)
    assert result["label"] is None
    assert result["candidate_label"] == "Positive-Food"
    assert result["review_required"] and result["abstained"]
    assert result["confidence_threshold_met"] is True
    assert result["production_validated"] is False
