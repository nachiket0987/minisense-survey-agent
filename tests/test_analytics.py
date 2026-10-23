from datetime import date
import pytest
from pydantic import ValidationError
from minisense.contracts import SurveyResponse, Period
from minisense.dataset import generate
from minisense.analytics import SurveyStore, compute_csat, compare


def test_generation():
    rows = generate(1000, seed=42)
    assert rows == generate(1000, seed=42)
    assert len({r["response_id"] for r in rows}) == 1000
    assert {r["date"][:7] for r in rows} == {"2026-05", "2026-06"}
    assert {r["sentiment"] for r in rows} == {
        "positive",
        "negative",
        "neutral",
        "mixed",
    }
    for row in rows:
        SurveyResponse.model_validate(row)
    assert len({r["free_text"] for r in rows}) > 100
    assert all(r["business_id"] == "b01" for r in rows)


def test_csat_and_empty():
    assert compute_csat([1, 3, 4, 5]) == {"mean": 3.25, "satisfied_pct": 50.0}
    assert compute_csat([]) == {"mean": None, "satisfied_pct": None}


def test_filter_themes():
    store = SurveyStore(generate(1000))
    period = Period(start="2026-06-01", end="2026-06-30")
    rows = store.select(period, "b01")
    out = store.metrics(period, "b01", theme="wait_time")
    assert out.count == len(rows)
    assert out.complaints["wait_time"] == sum(
        "wait_time" in r.complaint_themes for r in rows
    )
    assert store.metrics(period, "other").count == 0
    assert all(r.date.month == 6 for r in rows)


def test_compare_empty_and_small():
    store = SurveyStore(generate(20))
    may = store.metrics(Period(start="2026-05-01", end="2026-05-31"), "b01")
    june = store.metrics(Period(start="2026-06-01", end="2026-06-30"), "b01")
    empty = store.metrics(Period(start="2026-04-01", end="2026-04-30"), "b01")
    assert compare(empty, june).count_change_pct is None
    assert compare(may, june).count_delta == june.count - may.count
    assert compare(may, june).warnings


def test_validation():
    row = generate(1)[0]
    row["rating"] = 6
    with pytest.raises(ValidationError):
        SurveyResponse.model_validate(row)
    with pytest.raises(ValidationError):
        Period(start="2026-06-30", end="2026-06-01")


def test_empty_prevalence_is_undefined():
    result = SurveyStore(generate(10)).metrics(
        Period(start="2026-04-01", end="2026-04-30"), "b01"
    )
    assert all(v is None for v in result.complaint_rates.values())
