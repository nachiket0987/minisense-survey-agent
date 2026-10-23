"""Reproducible assessment data with clause families held out across four splits."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
from .finetune import LABELS

# Each row corresponds to LABELS in order. Entire clause families stay in one split.
TEMPLATES = {
    "train": (
        ("The food tasted fresh", "My meal was delicious", "The bowl had wonderful flavour", "I loved the tasty toast", "The ingredients were excellent", "The coffee tasted great", "The dish was not bland at all", "The food was cooked perfectly"),
        ("The food arrived cold", "My meal tasted stale", "The toast was burnt", "The bowl tasted awful", "The ingredients seemed spoiled", "The coffee tasted bitter and unpleasant", "The food was not fresh", "The dish was undercooked"),
        ("The queue moved too slowly", "I waited far too long", "My order took ages to arrive", "The wait time was unacceptable", "Preparing the food was painfully slow", "The line barely moved", "My meal was delayed for too long", "Service was not quick enough"),
        ("The staff were very helpful", "The cashier was kind", "Our server was friendly", "The team treated us politely", "The employee patiently answered my questions", "The manager was welcoming", "The staff were not rude at all", "The service team was attentive"),
        ("The staff were rude", "The cashier ignored my question", "Our server was dismissive", "The employee was unfriendly", "The manager spoke disrespectfully", "The team refused to help", "The staff were not polite", "The service team was inattentive"),
        ("My order was missing an item", "They gave me the wrong meal", "The coffee I paid for was forgotten", "My takeaway bag was incomplete", "I received someone else's order", "They ignored my requested substitution", "The order did not match my receipt", "The kitchen mixed up my order"),
        ("The portion was too small for the price", "The meal was overpriced", "The food was not worth the money", "I paid too much for so little", "The prices were unreasonable", "The serving was poor value", "The bill felt excessive", "The meal was not good value"),
        ("I ordered lunch at the bistro", "I collected a takeaway bag", "The menu listed several dishes", "I visited with a colleague", "My receipt showed the items ordered", "I bought a coffee to take away", "The restaurant had counter seating", "I placed my order at the till"),
    ),
    "validation": (
        ("The salad was crisp and appetising", "My breakfast was full of flavour", "I enjoyed every bite of the dish"),
        ("The soup had gone lukewarm", "The pastry tasted old", "My breakfast was unpleasant to eat"),
        ("I spent my break standing in line", "Getting served took much longer than expected", "The kitchen kept me waiting"),
        ("The person serving us was courteous", "The cashier gladly explained the choices", "The team made us feel welcome"),
        ("The person serving us was impolite", "The cashier brushed off my request", "The team made us feel unwelcome"),
        ("The side dish I ordered was absent", "My bag contained a different sandwich", "The items on the tray were not mine"),
        ("Such a small helping should cost less", "The amount charged was too high", "I expected more food for that cost"),
        ("I stopped by the dining area", "I ordered from the printed menu", "Our group visited the counter"),
    ),
    "calibration": (
        ("The toast was tasty and well prepared", "The flavours in my bowl were lovely", "The coffee was enjoyable"),
        ("The toast was dry and tasteless", "The bowl was poorly prepared", "The coffee was undrinkable"),
        ("The delay before collection was frustrating", "The order was not ready on time", "Waiting for the meal felt endless"),
        ("The employee was considerate and professional", "The server listened carefully", "The manager handled my question graciously"),
        ("The employee was inconsiderate and abrupt", "The server would not listen", "The manager handled my question rudely"),
        ("Part of the purchase was left out", "The wrong drink was packed", "My special request was not included in the order"),
        ("The price did not justify the portion", "The serving size was disappointing for the money", "The cost of the meal felt inflated"),
        ("The menu included bowls and drinks", "I kept the receipt after paying", "I collected the bag from the pickup point"),
    ),
    "test": (
        ("The meal was genuinely appetizing", "The ingredients tasted beautifully fresh", "There was nothing bland about the food", "I was pleased with the taste of my lunch"),
        ("The meal was badly overcooked", "The ingredients did not taste fresh", "I could not enjoy the flavour of the food", "The dish tasted unpleasant and old"),
        ("The time spent queuing ruined my lunch break", "I was disappointed by how slowly orders were prepared", "The pickup delay was excessive", "I could not get my food within a reasonable time"),
        ("Everyone behind the counter treated us kindly", "The person taking payment was patient and helpful", "The service staff were considerate", "I appreciated the team's welcoming manner"),
        ("Everyone behind the counter treated us dismissively", "The person taking payment was impatient and hostile", "The service staff were discourteous", "I disliked the team's unwelcoming manner"),
        ("The bag did not contain everything I had purchased", "I asked for one item but was handed another", "They omitted the extra side I had paid for", "My instructions about the order were missed"),
        ("The quantity of food did not justify what I spent", "I did not receive enough for the amount paid", "The charge was far too much for this serving", "The meal offered little value for my money"),
        ("Our party used the takeaway counter", "I chose a dish from the board", "The printed receipt contained my purchase", "I visited the restaurant with my family"),
    ),
}
PREFIXES = ("At lunch, ", "After work, ", "On my visit, ", "For takeaway, ",
            "When dining in, ", "On a weekend, ", "At the counter, ", "During breakfast, ",
            "While visiting with a friend, ", "On my first visit, ", "At this bistro, ", "Yesterday, ")
SUFFIXES = (".", ". That was my experience.", ". I am sharing this feedback.", ". This happened during my visit.")


def generate_splits(train_per_class=200, evaluation_per_class=64, test_per_class=100, seed=42):
    rng = random.Random(seed)
    splits = {}
    for split, bank in TEMPLATES.items():
        count = train_per_class if split == "train" else test_per_class if split == "test" else evaluation_per_class
        rows = []
        for label_id, (label, clauses) in enumerate(zip(LABELS, bank)):
            combinations = list(itertools.product(range(len(clauses)), PREFIXES, SUFFIXES))
            if not 1 <= count <= len(combinations):
                raise ValueError("Per-class count must be positive and fit the available unique template combinations")
            rng.shuffle(combinations)
            for index, (family, prefix, suffix) in enumerate(combinations[:count]):
                clause = clauses[family]
                clause = clause if clause.startswith("I ") else clause[0].lower() + clause[1:]
                if label_id in (1, 2, 4, 5, 6) and index % 5 == 0:
                    # One negative topic takes precedence over a positive mention.
                    prefix += "although the staff were friendly, " if label_id in (1, 6) else "although the food tasted good, "
                rows.append({"text": prefix + clause + suffix, "label": label,
                             "group": f"{split}/{label}/{family}"})
        rng.shuffle(rows)
        splits[split] = rows
    return splits


def write_splits(output, **kwargs):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Synthetic output directory must be absent or empty")
    splits = generate_splits(**kwargs)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"provenance": "synthetic template-generated assessment benchmark, not human-reviewed",
                "seed": kwargs.get("seed", 42), "template_families_disjoint": True, "splits": {}}
    for split, rows in splits.items():
        path = output / f"{split}.jsonl"
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8", newline="\n")
        manifest["splits"][split] = {"count": len(rows), "families": len({r["group"] for r in rows}),
                                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(write_splits(args.output)))
