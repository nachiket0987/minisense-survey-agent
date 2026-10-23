"""Local, reusable shadow inference. Unvalidated models never issue final labels."""
import json
import math
from pathlib import Path


def validate_text(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 10000:
        raise ValueError("Require nonblank text of at most 10000 characters")
    return text.strip()


def validate_policy(policy):
    if not isinstance(policy, dict):
        raise ValueError("Confidence policy must be an object")
    for name, lower, upper in (("temperature", 0.01, 100), ("threshold", 0, 1.01)):
        value = policy.get(name)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"Invalid confidence {name}")
        if value < lower or value > upper or (name == "temperature" and value == 0):
            raise ValueError(f"Invalid confidence {name}")
    return policy


def review_decision(candidate, confidence, threshold):
    return {"label": None, "candidate_label": candidate, "confidence": confidence,
            "confidence_threshold_met": confidence >= threshold,
            "abstained": True, "review_required": True,
            "reason": "checkpoint_not_production_validated", "mode": "shadow",
            "production_validated": False}


class ClassifierRuntime:
    """Instantiate once per worker; local CPU only, no downloads or text logging.

    Confidence is diagnostic, never deployment authorization. Even a checkpoint
    claiming production validation in its metadata cannot bypass human review.
    """

    def __init__(self, checkpoint):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from .finetune import LABELS

        path = Path(checkpoint)
        policy_path = path / "confidence_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {
            "temperature": 1.0, "threshold": 0.8}
        self.policy = validate_policy(policy)
        torch.set_num_threads(2)
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).to("cpu").eval()
        if self.model.config.num_labels != len(LABELS) or [
            self.model.config.id2label.get(i) for i in range(len(LABELS))
        ] != list(LABELS):
            raise ValueError("Checkpoint does not use the MiniSense eight-label taxonomy")

    def predict(self, text):
        import torch
        from .finetune import LABELS

        text = validate_text(text)
        encoded = self.tokenizer(text, return_tensors="pt", truncation=False)
        if encoded["input_ids"].shape[-1] > 128:
            raise ValueError("Text exceeds the trained 128-token limit; send for human review")
        with torch.inference_mode():
            logits = self.model(**encoded).logits
            if not torch.isfinite(logits).all():
                raise ValueError("Classifier returned nonfinite logits; send for human review")
            probabilities = torch.softmax(logits / self.policy["temperature"], dim=-1)
            if not torch.isfinite(probabilities).all():
                raise ValueError("Classifier returned nonfinite probabilities; send for human review")
            confidence, candidate = probabilities.max(dim=-1)
        return review_decision(LABELS[candidate.item()], confidence.item(), self.policy["threshold"])
