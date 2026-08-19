import csv
from pathlib import Path
import matplotlib.pyplot as plt


BASE = Path("/mnt/c/Projects/PathProbe-AI")

RESULT_FILE = BASE / "dataset/results/adaptive_vs_fixed.csv"
OUTPUT_DIR = BASE / "dataset/results/figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULT_FILE, newline="") as f:
        return list(csv.DictReader(f))


def plot_probe_comparison(rows):
    environments = [r["environment"] for r in rows]

    adaptive = [
        int(r["adaptive_probes"])
        for r in rows
    ]

    fixed = [
        int(r["fixed_probes"])
        for r in rows
    ]

    x = range(len(environments))

    width = 0.35

    plt.figure(figsize=(9, 6))

    plt.bar(
        [i - width / 2 for i in x],
        adaptive,
        width=width,
        label="Adaptive"
    )

    plt.bar(
        [i + width / 2 for i in x],
        fixed,
        width=width,
        label="Fixed"
    )

    plt.xticks(
        list(x),
        environments
    )

    plt.ylabel("Number of Probes")
    plt.xlabel("Environment")
    plt.title(
        "PathProbe-AI: Adaptive vs Fixed Probe Count"
    )

    plt.legend()
    plt.grid(axis="y", alpha=0.25)

    plt.tight_layout()

    path = OUTPUT_DIR / "probe_comparison.png"

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {path}")


def plot_probe_reduction(rows):
    environments = [r["environment"] for r in rows]

    reductions = []

    for r in rows:

        fixed = int(r["fixed_probes"])
        adaptive = int(r["adaptive_probes"])

        reduction = (
            (fixed - adaptive)
            / fixed
            * 100
        )

        reductions.append(reduction)

    x = range(len(environments))

    plt.figure(figsize=(9, 6))

    bars = plt.bar(
        x,
        reductions
    )

    plt.xticks(
        list(x),
        environments
    )

    plt.ylabel("Probe Reduction (%)")
    plt.xlabel("Environment")

    plt.title(
        "PathProbe-AI: Probe Reduction by Environment"
    )

    plt.axhline(
        sum(reductions) / len(reductions),
        linestyle="--",
        label=(
            f"Average = "
            f"{sum(reductions) / len(reductions):.2f}%"
        )
    )

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.25
    )

    for bar, value in zip(
        bars,
        reductions
    ):

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}%",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()

    path = OUTPUT_DIR / "probe_reduction.png"

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {path}")


def plot_accuracy(rows):
    environments = [r["environment"] for r in rows]

    adaptive_correct = [
        r["adaptive_diagnosis"]
        == r["actual"]
        for r in rows
    ]

    fixed_correct = [
        r["fixed_diagnosis"]
        == r["actual"]
        for r in rows
    ]

    adaptive_accuracy = [
        100 if value else 0
        for value in adaptive_correct
    ]

    fixed_accuracy = [
        100 if value else 0
        for value in fixed_correct
    ]

    x = range(len(environments))

    width = 0.35

    plt.figure(figsize=(9, 6))

    plt.bar(
        [i - width / 2 for i in x],
        adaptive_accuracy,
        width=width,
        label="Adaptive"
    )

    plt.bar(
        [i + width / 2 for i in x],
        fixed_accuracy,
        width=width,
        label="Fixed"
    )

    plt.xticks(
        list(x),
        environments
    )

    plt.ylim(0, 110)

    plt.ylabel("Classification Accuracy (%)")
    plt.xlabel("Environment")

    plt.title(
        "PathProbe-AI: Classification Accuracy"
    )

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    path = OUTPUT_DIR / "classification_accuracy.png"

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {path}")


def main():

    print()
    print("========================================")
    print("   PATHPROBE-AI RESULT VISUALIZATION")
    print("========================================")

    if not RESULT_FILE.exists():

        raise FileNotFoundError(
            f"Result file not found:\n{RESULT_FILE}"
        )

    rows = load_results()

    print(
        f"Loaded {len(rows)} environment results."
    )

    plot_probe_comparison(rows)

    plot_probe_reduction(rows)

    plot_accuracy(rows)

    print()
    print("========================================")
    print("       VISUALIZATION COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
