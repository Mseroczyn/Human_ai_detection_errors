"""Reproduce the analysis from the curated game-level data. No API calls."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MIN_WORDS = 50
BOOTSTRAPS = 10_000
SEED = 20261016


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def participant_groups(games):
    """Keep together games sharing any participant, including across roles."""
    parent = {}

    def find(person):
        parent.setdefault(person, person)
        if parent[person] != person:
            parent[person] = find(parent[person])
        return parent[person]

    for game in games:
        a = find(game["interrogator_id"])
        b = find(game["human_witness_id"])
        parent[a] = b

    groups = defaultdict(list)
    for index, game in enumerate(games):
        groups[find(game["interrogator_id"])].append(index)
    ordered = sorted(groups.values(), key=lambda g: min(games[i]["game_id"] for i in g))
    group_id = np.empty(len(games), dtype=int)
    for index, members in enumerate(ordered):
        group_id[members] = index
    return group_id, len(ordered), len(parent)


def main():
    with (ROOT / "data/games.csv").open(encoding="utf-8", newline="") as handle:
        source = sorted(csv.DictReader(handle), key=lambda r: int(r["game_id"]))
    assert len({r["game_id"] for r in source}) == len(source)
    games = [
        r.copy() for r in source
        if int(r["gpt5_words"]) >= MIN_WORDS and int(r["human_words"]) >= MIN_WORDS
    ]
    for game in games:
        for key in ["human_correct", "gpt5_words", "human_words"]:
            game[key] = int(game[key])
        assert game["human_correct"] in [0, 1]
        for witness in ["gpt5", "human"]:
            assert game[f"{witness}_verdict"] in ["AI", "Human", "Mixed"]
            key = f"{witness}_human_written_share"
            game[key] = float(game[key])
            assert 0 <= game[key] <= 1
        human_share = game["human_human_written_share"]
        ai_share = game["gpt5_human_written_share"]
        game["pair_order"] = (
            "Correct" if human_share > ai_share else
            "Reversed" if human_share < ai_share else "Tied"
        )
        game["pair_credit"] = {"Correct": 1.0, "Tied": 0.5, "Reversed": 0.0}[game["pair_order"]]

    group_id, group_count, person_count = participant_groups(games)
    for game, group in zip(games, group_id):
        game["component_id"] = f"C{group + 1:03d}"
    # Each draw resamples whole groups. The same draws are used for every metric.
    rng = np.random.default_rng(SEED)
    draws = rng.multinomial(
        group_count, np.full(group_count, 1 / group_count), size=BOOTSTRAPS
    )
    estimates, bootstrap_values = {}, {}

    def rate(name, numerator, denominator):
        numerator = np.asarray(numerator, dtype=float)
        denominator = np.asarray(denominator, dtype=float)
        group_num = np.bincount(group_id, weights=numerator, minlength=group_count)
        group_den = np.bincount(group_id, weights=denominator, minlength=group_count)
        sample_den = draws @ group_den
        assert np.all(sample_den > 0), "A bootstrap draw has an empty denominator."
        samples = (draws @ group_num) / sample_den
        low, high = np.quantile(samples, [0.05, 0.95])
        estimates[name] = {
            "metric": name,
            "estimate": float(numerator.sum() / denominator.sum()),
            "ci90_low": float(low),
            "ci90_high": float(high),
            "numerator": float(numerator.sum()),
            "denominator": int(denominator.sum()),
            "degenerate_interval": bool(np.ptp(samples) == 0),
        }
        bootstrap_values[name] = samples

    def difference(name, left, right):
        samples = bootstrap_values[left] - bootstrap_values[right]
        low, high = np.quantile(samples, [0.05, 0.95])
        estimates[name] = {
            "metric": name,
            "estimate": estimates[left]["estimate"] - estimates[right]["estimate"],
            "ci90_low": float(low),
            "ci90_high": float(high),
            "numerator": None,
            "denominator": len(games),
            "degenerate_interval": bool(np.ptp(samples) == 0),
        }

    correct = np.array([g["human_correct"] for g in games])
    fooled = 1 - correct
    one = np.ones(len(games))
    credit = np.array([g["pair_credit"] for g in games])
    ai_flag = np.array([g["gpt5_verdict"] == "AI" for g in games], dtype=int)
    human_flag = np.array([g["human_verdict"] == "AI" for g in games], dtype=int)
    human_mixed = np.array([g["human_verdict"] == "Mixed" for g in games], dtype=int)
    human_ok = np.array([g["human_verdict"] == "Human" for g in games], dtype=int)

    masks = {"overall": one, "human_correct": correct, "human_fooled": fooled}
    for group, mask in masks.items():
        rate(f"paired_credit_{group}", credit * mask, mask)
        rate(f"gpt5_ai_flag_{group}", ai_flag * mask, mask)
        rate(f"gpt5_nondetection_{group}", (1 - ai_flag) * mask, mask)
    rate("human_ai_only_false_positive_overall", human_flag, one)
    rate("human_mixed_overall", human_mixed, one)
    rate("strict_document_accuracy_overall", ai_flag + human_ok, 2 * one)
    difference(
        "paired_difference_fooled_minus_correct",
        "paired_credit_human_fooled", "paired_credit_human_correct",
    )
    difference(
        "ai_flag_difference_fooled_minus_correct",
        "gpt5_ai_flag_human_fooled", "gpt5_ai_flag_human_correct",
    )

    overlap = []
    for label, mask in [("People correct", correct), ("People fooled", fooled)]:
        counts = Counter(g["pair_order"] for g, keep in zip(games, mask) if keep)
        overlap.append({
            "human_judgment": label,
            "correct_ordering": counts["Correct"],
            "tied": counts["Tied"],
            "reversed_ordering": counts["Reversed"],
            "total": int(mask.sum()),
        })
    classification = []
    for witness in ["gpt5", "human"]:
        counts = Counter(g[f"{witness}_verdict"] for g in games)
        classification.append({
            "known_source": witness,
            "AI": counts["AI"], "Human": counts["Human"],
            "Mixed": counts["Mixed"], "total": len(games),
        })

    sample = {
        "paper_gpt5_games": 150,
        "available_gpt5_games": len(source),
        "available_human_fooled": sum(1 - int(g["human_correct"]) for g in source),
        "minimum_words_per_witness": MIN_WORDS,
        "excluded_games": len(source) - len(games),
        "retained_games": len(games),
        "human_correct_games": int(correct.sum()),
        "human_fooled_games": int(fooled.sum()),
        "texts": 2 * len(games),
        "input_words": sum(g["gpt5_words"] + g["human_words"] for g in games),
        "unique_people": person_count,
        "participant_groups": group_count,
        "bootstrap_replicates": BOOTSTRAPS,
        "bootstrap_seed": SEED,
        "minimum_ai_flags_among_human_fooled_given_overall_accuracy": max(
            0, int(ai_flag.sum() - correct.sum())
        ),
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    write_csv(results / "paired_results.csv", games)
    write_csv(results / "estimates.csv", list(estimates.values()))
    write_csv(results / "overlap_table.csv", overlap)
    write_csv(results / "classification_table.csv", classification)
    (results / "summary.json").write_text(
        json.dumps({"sample": sample, "estimates": estimates, "overlap": overlap,
                    "classification": classification}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(source)} available games -> {len(games)} retained; "
          f"{int(fooled.sum())} people-fooled, {int(correct.sum())} people-correct.")
    print(f"GPT-5 AI flags: {int(ai_flag.sum())}/{len(games)} overall; "
          f"{int((ai_flag * fooled).sum())}/{int(fooled.sum())} when people were fooled.")


if __name__ == "__main__":
    main()
