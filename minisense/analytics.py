import json
from collections import Counter
from pathlib import Path
from .contracts import SurveyResponse, Period, Metrics, Comparison, THEMES


def compute_csat(ratings: list[int]) -> dict:
    if not ratings:
        return {"mean": None, "satisfied_pct": None}
    return {
        "mean": sum(ratings) / len(ratings),
        "satisfied_pct": 100 * sum(r >= 4 for r in ratings) / len(ratings),
    }


class SurveyStore:
    def __init__(self, rows: list[dict]):
        self.rows = [SurveyResponse.model_validate(r) for r in rows]
        if not self.rows:
            raise ValueError("Survey dataset is empty")
        if len({r.response_id for r in self.rows}) != len(self.rows):
            raise ValueError("Duplicate response IDs")
        self.latest = max(r.date for r in self.rows)

    @classmethod
    def load(cls, path: Path):
        if not path.exists():
            raise FileNotFoundError(
                f"Dataset missing: run python -m minisense generate ({path})"
            )
        return cls(json.loads(path.read_text(encoding="utf-8"))["responses"])

    def select(self, period: Period, business_id: str):
        return [
            r
            for r in self.rows
            if r.business_id == business_id and period.start <= r.date <= period.end
        ]

    def metrics(
        self, period: Period, business_id: str, theme: str | None = None, top_n: int = 3
    ) -> Metrics:
        rows = self.select(period, business_id)
        csat = compute_csat([r.rating for r in rows])
        themes = Counter(t for r in rows for t in r.themes)
        complaints = Counter(t for r in rows for t in r.complaint_themes)
        names = [theme] if theme else list(THEMES)
        counts = {t: complaints[t] for t in names}
        return Metrics(
            period=period,
            business_id=business_id,
            count=len(rows),
            mean_rating=csat["mean"],
            satisfied_pct=csat["satisfied_pct"],
            themes={t: themes[t] for t in names},
            complaints=counts,
            complaint_rates={
                t: 100 * n / len(rows) if rows else None for t, n in counts.items()
            },
            top_complaints=sorted(
                ((t, n) for t, n in counts.items() if n), key=lambda x: (-x[1], x[0])
            )[:top_n],
        )


def relative(before, after):
    return 100 * (after - before) / before if before else None


def compare(before: Metrics, after: Metrics) -> Comparison:
    if (
        before.business_id != after.business_id
        or before.period.end >= after.period.start
    ):
        raise ValueError(
            "Compare ordered non-overlapping periods for the same business"
        )
    names = set(before.complaints) | set(after.complaints)
    warnings = []
    if min(before.count, after.count) < 30:
        warnings.append(
            "At least one period has fewer than 30 responses; interpret cautiously."
        )
    if not before.count or not after.count:
        warnings.append("A period is empty; prevalence changes are undefined.")
    changes = {
        t: dict(
            count_delta=after.complaints.get(t, 0) - before.complaints.get(t, 0),
            change_pct=relative(
                before.complaints.get(t, 0), after.complaints.get(t, 0)
            ),
            rate_delta_pp=(
                after.complaint_rates.get(t, 0) - before.complaint_rates.get(t, 0)
                if before.count and after.count
                else None
            ),
        )
        for t in sorted(names)
    }
    return Comparison(
        earlier=before.period,
        later=after.period,
        count_delta=after.count - before.count,
        count_change_pct=relative(before.count, after.count),
        mean_delta=(
            after.mean_rating - before.mean_rating
            if before.mean_rating is not None and after.mean_rating is not None
            else None
        ),
        complaints=changes,
        warnings=warnings,
    )
