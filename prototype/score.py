"""
Deterministic scorer for the proposal triage design.

AI reads, code decides: this file takes facts already extracted by the model
(facts.json) and the admin's criteria (criteria.json), then applies the
mandatory gate, the weighted formulas and the ranking. No model call happens
here, so the same inputs always give the same output.

Usage:
    python score.py                  # uses facts.json and criteria.json
    python score.py --explain        # also prints the per criterion breakdown
"""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).parent


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def mandatory_failures(facts):
    failures = []
    if facts.get("licence_held_by_bidder") is not True:
        failures.append("licence not held by the bidder")
    if facts.get("wsib_clearance") is not True:
        failures.append("WSIB clearance not confirmed")
    if facts.get("liability_5m") is not True:
        failures.append("$5M liability insurance not confirmed")
    return failures


def budget_and_time_failures(facts, criteria):
    """Hard limits from the category itself, separate from the weighted criteria."""
    failures = []
    price = facts.get("total_price_cad")
    if is_number(price) and price > criteria["budget_ceiling_cad"]:
        failures.append("price above budget ceiling")
    weeks = facts.get("completion_weeks")
    if is_number(weeks) and weeks > criteria["max_weeks"]:
        failures.append("timeline longer than the allowed weeks")
    return failures


def score_criterion(crit, facts, pool):
    weight = crit["weight"]
    method = crit["method"]

    if method == "count_capped":
        value = facts.get(crit["field"])
        if not is_number(value):
            return 0.0, "not stated"
        points = min(value, crit["cap"]) / crit["cap"] * weight
        return points, f"{value} qualifying installs (cap {crit['cap']})"

    if method == "lowest_is_best":
        value = facts.get(crit["field"])
        if not is_number(value):
            return 0.0, "not stated, scored 0"
        best = min(p[crit["field"]] for p in pool if is_number(p.get(crit["field"])))
        return best / value * weight, f"{value} vs best {best}"

    if method == "sum_of_parts":
        share = weight / len(crit["fields"])
        points, parts = 0.0, []
        for field in crit["fields"]:
            value = facts.get(field)
            if not is_number(value):
                parts.append(f"{field} not stated")
                continue
            best = max(p[field] for p in pool if is_number(p.get(field)))
            points += value / best * share
            parts.append(f"{field.split('_')[0]} {value}y")
        return points, ", ".join(parts)

    if method == "checklist":
        share = weight / len(crit["fields"])
        present = [f for f in crit["fields"] if facts.get(f) is True]
        missing = [f for f in crit["fields"] if f not in present]
        note = "missing: " + ", ".join(missing) if missing else "all items present"
        return len(present) * share, note

    raise ValueError(f"Unknown scoring method: {method}")


def run(criteria, all_facts):
    results = {}

    # Step 1: mandatory gate and hard limits (rules only)
    eligible = {}
    for letter, facts in all_facts.items():
        if letter.startswith("_"):
            continue
        fails = mandatory_failures(facts) + budget_and_time_failures(facts, criteria)
        if fails:
            results[letter] = {"status": "ineligible", "fails": fails}
        else:
            eligible[letter] = facts

    # Step 2: score every eligible proposal on merit, including flagged ones,
    # so the reviewer can see what the flag did or did not change.
    pool = list(eligible.values())
    for letter, facts in eligible.items():
        breakdown, total = {}, 0.0
        for crit in criteria["weighted"]:
            points, why = score_criterion(crit, facts, pool)
            breakdown[crit["id"]] = {"points": round(points, 2), "why": why}
            total += points
        status = "flagged" if facts.get("suspicious_instructions") else "ranked"
        results[letter] = {"status": status, "score": round(total, 1), "breakdown": breakdown}

    # Step 3: rank only clean proposals; ties broken by letter so order is stable
    ranked = sorted(
        (l for l, r in results.items() if r["status"] == "ranked"),
        key=lambda l: (-results[l]["score"], l),
    )
    for position, letter in enumerate(ranked, start=1):
        results[letter]["rank"] = position

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--facts", default=HERE / "facts.json")
    parser.add_argument("--criteria", default=HERE / "criteria.json")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()

    criteria = json.loads(Path(args.criteria).read_text())
    facts = json.loads(Path(args.facts).read_text())
    results = run(criteria, facts)

    print(f"Criteria version {criteria['version']} ({criteria['category']})\n")
    order = sorted(results, key=lambda l: (results[l].get("rank") or 99, l))
    for letter in order:
        r = results[letter]
        if r["status"] == "ineligible":
            print(f"{letter}: INELIGIBLE ({'; '.join(r['fails'])})")
            continue
        label = f"rank {r['rank']}" if r["status"] == "ranked" else "FLAGGED, held for human review"
        print(f"{letter}: {label}, merit score {r['score']}")
        if args.explain:
            for cid, item in r["breakdown"].items():
                print(f"    {cid:<11}{item['points']:>6}   {item['why']}")


if __name__ == "__main__":
    main()
