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
    assert output["label"] in LABELS
    assert output["production_validated"] is False
