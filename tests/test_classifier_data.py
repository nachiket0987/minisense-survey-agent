from collections import Counter
import pytest


def test_synthetic_splits_are_reproducible_balanced_and_family_disjoint():
    from minisense.classifier_data import generate_splits, TEMPLATES
    from minisense.finetune import LABELS, validate_splits

    splits = generate_splits(train_per_class=16, evaluation_per_class=8, test_per_class=8)
    assert splits == generate_splits(train_per_class=16, evaluation_per_class=8, test_per_class=8)
    assert set(splits) == {"train", "validation", "calibration", "test"}
    for split, rows in splits.items():
        assert Counter(r["label"] for r in rows) == {label: 16 if split == "train" else 8 for label in LABELS}
    families = []
    for bank in TEMPLATES.values():
        families.append({text for alternatives in bank for text in alternatives})
    for i, current in enumerate(families):
        assert all(not current & earlier for earlier in families[:i])
    validate_splits(splits["train"], splits["validation"], splits["test"], splits["calibration"])


def test_synthetic_generator_refuses_invalid_counts():
    from minisense.classifier_data import generate_splits
    with pytest.raises(ValueError):
        generate_splits(train_per_class=0)
    with pytest.raises(ValueError):
        generate_splits(train_per_class=1000000)
