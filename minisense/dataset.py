"""Reproducible synthetic data with explicit mention-level ground truth."""

import calendar
import json
import random
from pathlib import Path
from .contracts import THEMES

PHRASES = {
    "food_quality": (
        "The {item} tasted fresh",
        "The {item} arrived cold",
        "The {item} tasted ordinary",
    ),
    "wait_time": (
        "My order was ready quickly",
        "The queue moved too slowly",
        "The wait was about what I expected",
    ),
    "staff_service": (
        "The staff were helpful",
        "The staff seemed dismissive",
        "The service was routine",
    ),
    "order_accuracy": (
        "My order was exactly right",
        "My order was missing an item",
        "My order needed a minor clarification",
    ),
    "cleanliness": (
        "The tables looked spotless",
        "My table had not been cleaned",
        "The dining area looked acceptable",
    ),
    "value": (
        "The meal felt worth the price",
        "The portion felt too small for the price",
        "The pricing seemed average",
    ),
    "satisfaction": (
        "I enjoyed the overall visit",
        "The visit was disappointing",
        "The visit was neither good nor bad",
    ),
}


def generate(count: int = 100000, seed: int = 42) -> list[dict]:
    if count < 1:
        raise ValueError("Count must be positive")
    rng = random.Random(seed)
    prose_rng = random.Random(seed + 1)
    rows = []
    for i in range(count):
        month = 5 if i < round(count * 0.47) else 6
        sentiment = rng.choices(
            ["positive", "negative", "neutral", "mixed"],
            weights=[52 if month == 5 else 40, 21 if month == 5 else 30, 12, 15],
        )[0]
        theme = rng.choices(
            THEMES, weights=[22, 18 if month == 5 else 32, 15, 12, 8, 15, 10]
        )[0]
        themes = [theme]
        complaints = [theme] if sentiment in ("negative", "mixed") else []
        polarities = [1 if complaints else (0 if sentiment == "positive" else 2)]
        if sentiment == "mixed":
            second = rng.choice([t for t in THEMES if t != theme])
            themes.append(second)
            polarities.append(0)
        rating = rng.choices(
            [1, 2, 3, 4, 5],
            weights={
                "positive": [0, 0, 2, 35, 63],
                "negative": [27, 50, 23, 0, 0],
                "neutral": [0, 8, 80, 12, 0],
                "mixed": [0, 15, 60, 25, 0],
            }[sentiment],
        )[0]
        item = rng.choice(["Avocado Toast", "Garden Bowl", "Cold Brew Coffee"])
        text = "; ".join(
            PHRASES[t][p].format(item=item) for t, p in zip(themes, polarities)
        )
        text += rng.choice(
            [
                " during my lunch visit.",
                " after work.",
                " when I stopped in with a friend.",
                " on my takeaway order.",
                " during a weekend visit.",
                ".",
            ]
        )
        text += f' I ordered {prose_rng.choice(["Avocado Toast","Garden Bowl","Cold Brew Coffee"])} at {prose_rng.randint(8,20):02}:{prose_rng.choice(["00","15","30","45"])} {prose_rng.choice(["on my own","with family","with colleagues","with a friend"])}.'
        rows.append(
            dict(
                response_id=f"r{i+1:06}",
                date=f"2026-{month:02}-{rng.randint(1,calendar.monthrange(2026,month)[1]):02}",
                business_id="b01",
                business_name="GreenLeaf Bistro",
                survey_id="s01",
                survey_name="Customer Experience",
                rating=rating,
                response_channel=rng.choices(
                    ["mobile", "web", "in_store"], [50, 30, 20]
                )[0],
                free_text=text,
                sentiment=sentiment,
                themes=themes,
                complaint_themes=complaints,
            )
        )
    rng.shuffle(rows)
    return rows


def write_dataset(path: Path, count: int = 100000, seed: int = 42):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"responses": generate(count, seed)}, ensure_ascii=False),
        encoding="utf-8",
    )
