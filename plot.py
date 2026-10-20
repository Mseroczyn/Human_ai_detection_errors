"""Create the two-panel figure from analyse.py's outputs."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parent
COLORS = {
    "teal": "#19AEAF", "pink": "#E03D90", "coral": "#FC744C",
    "text": "#090C0C", "secondary": "#5C737B", "ticks": "#2B424B",
    "grid": "#E2EEEE", "axis": "#90A5AB",
}


def main():
    summary = json.loads((ROOT / "results/summary.json").read_text())
    estimates = summary["estimates"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 11,
        "text.color": COLORS["text"],
        "xtick.color": COLORS["ticks"], "ytick.color": COLORS["ticks"],
        "axes.edgecolor": COLORS["axis"], "axes.linewidth": 0.7,
        "axes.facecolor": "white", "figure.facecolor": "white",
        "svg.fonttype": "none", "pdf.fonttype": 42,
    })
    fig = plt.figure(figsize=(12.4, 6.7))
    left = fig.add_axes([0.065, 0.36, 0.395, 0.59])
    right = fig.add_axes([0.590, 0.36, 0.375, 0.59])
    for ax in [left, right]:
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=COLORS["grid"], linewidth=0.8)
        ax.tick_params(axis="both", length=0, pad=8)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        for side in ["top", "right", "left"]:
            ax.spines[side].set_visible(False)

    with (ROOT / "results/paired_results.csv").open(newline="") as handle:
        games = list(csv.DictReader(handle))
    figure_rows = []

    def bar(ax, x, metric, color, panel):
        row = estimates[metric]
        value, low, high = [
            100 * row[key] for key in ["estimate", "ci90_low", "ci90_high"]
        ]
        # A resampled zero-error group cannot reveal unseen errors. Do not show
        # its zero-width bootstrap interval as a population-risk bound.
        degenerate = row["degenerate_interval"]
        ax.bar(x, value, width=0.56, color=COLORS[color], zorder=3)
        if degenerate:
            ax.scatter(x, value, color=COLORS[color], s=28, zorder=5, clip_on=False)
        else:
            ax.errorbar(
                x, value, yerr=[[value - low], [high - value]], fmt="none",
                ecolor=COLORS["ticks"], elinewidth=1, capsize=3, zorder=4,
            )
        suffix = "†" if degenerate else ""
        ax.text(
            x, high + (2.5 if panel == "A" else 0.55), f"{value:.1f}%{suffix}",
            ha="center", fontsize=11.5, fontweight="bold",
        )
        figure_rows.append({
            "panel": panel, **row,
            "estimate_percent": value, "ci90_low_percent": low,
            "ci90_high_percent": high,
        })
        return high

    for index, group in enumerate(["overall", "human_correct", "human_fooled"]):
        chosen = [
            g for g in games if group == "overall"
            or int(g["human_correct"]) == (1 if group == "human_correct" else 0)
        ]
        wins = sum(g["pair_order"] == "Correct" for g in chosen)
        ties = sum(g["pair_order"] == "Tied" for g in chosen)
        high = bar(
            left, index, f"paired_credit_{group}",
            "pink" if group == "human_fooled" else "teal", "A",
        )
        left.text(
            index, high + 7.5, f"Human higher: {wins}\nTies: {ties}",
            ha="center", fontsize=9, color=COLORS["secondary"],
            linespacing=1.15,
        )
    left.set(
        ylim=(0, 116), xlim=(-0.55, 2.55),
        yticks=[0, 25, 50, 75, 100], xticks=range(3),
        xticklabels=["All games\nn = 103", "People right\nn = 41",
                     "People wrong\nn = 62"],
    )
    left.axhline(50, color=COLORS["axis"], linewidth=0.8,
                 linestyle=(0, (4, 4)), zorder=2)

    error_metrics = [
        ("gpt5_nondetection_overall", "teal", "GPT-5 missed\nAll games"),
        ("gpt5_nondetection_human_fooled", "pink", "GPT-5 missed\nPeople wrong"),
        ("human_ai_only_false_positive_overall", "coral", "Human flagged AI\nAll games"),
    ]
    for index, (metric, color, label) in enumerate(error_metrics):
        high = bar(right, index, metric, color, "B")
        row = estimates[metric]
        right.text(
            index, high + 1.32, f"{int(row['numerator'])}/{row['denominator']}",
            ha="center", fontsize=9, color=COLORS["secondary"],
        )
    right.set(
        ylim=(0, 11), xlim=(-0.55, 2.55), yticks=[0, 2, 4, 6, 8, 10],
        xticks=range(3), xticklabels=[r[2] for r in error_metrics],
    )
    for ax in [left, right]:
        ax.tick_params(axis="x", labelsize=10)
    fig.text(
        0.2625, 0.238, "Pangram comparison score",
        ha="center", fontsize=13, fontweight="bold",
    )
    fig.text(
        0.2625, 0.197,
        "Comparing the share labelled human-written in each chat.\n"
        "Human chat higher = 1 point; tie = ½; GPT-5 higher = 0.",
        ha="center", va="top", fontsize=10.5, color=COLORS["ticks"],
        linespacing=1.4,
    )
    fig.text(
        0.7775, 0.238, "Pangram mistakes",
        ha="center", fontsize=13, fontweight="bold",
    )
    fig.text(
        0.7775, 0.197,
        "Missed GPT-5 texts or human texts wrongly labelled AI.\n"
        "Based on the report’s verdict; lower is better.",
        ha="center", va="top", fontsize=10.5, color=COLORS["ticks"],
        linespacing=1.4,
    )
    fig.text(
        0.035, 0.100,
        "Lines show 90% uncertainty intervals accounting for repeated participants. "
        "Five human 'mixed' verdicts are reported separately.",
        fontsize=9.2, color=COLORS["secondary"],
    )
    fig.text(
        0.035, 0.065,
        "†Zero observed misses does not imply perfect detection; no uncertainty bar is shown. "
        "Dashed line: 50% chance score.",
        fontsize=9.2, color=COLORS["secondary"],
    )
    fig.text(
        0.035, 0.025,
        "103 games. Sources: Jones & Bergen (2026), OSF jk7bw; "
        "Pangram 4.1, 19 October 2026.",
        fontsize=8.7, color=COLORS["secondary"],
    )
    folder = ROOT / "figures"
    folder.mkdir(exist_ok=True)
    for extension in ["png", "svg", "pdf"]:
        fig.savefig(folder / f"main_figure.{extension}", dpi=200, facecolor="white")
    plt.close(fig)
    with (ROOT / "results/figure_data.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(figure_rows[0]))
        writer.writeheader()
        writer.writerows(figure_rows)
    print("Wrote figures/main_figure.png, .svg, .pdf and results/figure_data.csv.")


if __name__ == "__main__":
    main()
