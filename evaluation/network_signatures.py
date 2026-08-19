import csv
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path("/mnt/c/Projects/PathProbe-AI")

INPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "raw"
    / "environment_observations.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "dataset"
    / "results"
    / "figures"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def load_data():
    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        rows = list(csv.DictReader(file))

    for row in rows:
        row["probe_value"] = float(row["probe_value"])
        row["packet_loss_percent"] = float(
            row["packet_loss_percent"]
        )
        row["throughput_mbps"] = float(
            row["throughput_mbps"]
        )
        row["average_delay_ms"] = float(
            row["average_delay_ms"]
        )

    return rows


def group_by_environment(rows):
    environments = {}

    for row in rows:
        environment = row["environment_id"]

        if environment not in environments:
            environments[environment] = []

        environments[environment].append(row)

    for environment in environments:
        environments[environment].sort(
            key=lambda x: x["probe_value"]
        )

    return environments


def plot_packet_loss(environments):
    plt.figure(figsize=(10, 6))

    for environment in ["E0", "E1", "E2"]:

        if environment not in environments:
            continue

        rows = environments[environment]

        x = [
            row["probe_value"]
            for row in rows
        ]

        y = [
            row["packet_loss_percent"]
            for row in rows
        ]

        plt.plot(
            x,
            y,
            marker="o",
            linewidth=2,
            label=environment,
        )

    plt.xlabel("Probe Rate (packets/sec)")
    plt.ylabel("Packet Loss (%)")

    plt.title(
        "PathProbe-AI: Packet Loss Response to Probe Rate"
    )

    plt.grid(
        True,
        alpha=0.25,
    )

    plt.legend()

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "network_signature_packet_loss.png"
    )

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {output}")


def plot_delay(environments):
    plt.figure(figsize=(10, 6))

    for environment in ["E0", "E1", "E2"]:

        if environment not in environments:
            continue

        rows = environments[environment]

        x = [
            row["probe_value"]
            for row in rows
        ]

        y = [
            row["average_delay_ms"]
            for row in rows
        ]

        plt.plot(
            x,
            y,
            marker="o",
            linewidth=2,
            label=environment,
        )

    plt.xlabel("Probe Rate (packets/sec)")
    plt.ylabel("Average Delay (ms)")

    plt.title(
        "PathProbe-AI: Delay Response to Probe Rate"
    )

    plt.grid(
        True,
        alpha=0.25,
    )

    plt.legend()

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "network_signature_delay.png"
    )

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {output}")


def plot_throughput(environments):
    plt.figure(figsize=(10, 6))

    for environment in ["E0", "E1", "E2"]:

        if environment not in environments:
            continue

        rows = environments[environment]

        x = [
            row["probe_value"]
            for row in rows
        ]

        y = [
            row["throughput_mbps"]
            for row in rows
        ]

        plt.plot(
            x,
            y,
            marker="o",
            linewidth=2,
            label=environment,
        )

    plt.xlabel("Probe Rate (packets/sec)")
    plt.ylabel("Throughput (Mbps)")

    plt.title(
        "PathProbe-AI: Throughput Response to Probe Rate"
    )

    plt.grid(
        True,
        alpha=0.25,
    )

    plt.legend()

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "network_signature_throughput.png"
    )

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {output}")


def print_signature_summary(environments):

    print()
    print("========================================")
    print("       NETWORK SIGNATURE SUMMARY")
    print("========================================")

    for environment in ["E0", "E1", "E2"]:

        if environment not in environments:
            continue

        rows = environments[environment]

        print()
        print(
            f"{environment} "
            f"({rows[0]['environment_name'].upper()})"
        )

        print("----------------------------------------")

        for row in rows:

            print(
                f"{int(row['probe_value']):>4} pps | "
                f"Loss: "
                f"{row['packet_loss_percent']:>6.2f}% | "
                f"Delay: "
                f"{row['average_delay_ms']:>7.2f} ms | "
                f"Throughput: "
                f"{row['throughput_mbps']:>8.4f} Mbps"
            )


def main():

    print()
    print("========================================")
    print("      PATHPROBE-AI")
    print("      NETWORK SIGNATURE ANALYSIS")
    print("========================================")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_FILE}"
        )

    rows = load_data()

    print(
        f"Loaded {len(rows)} observations."
    )

    environments = group_by_environment(rows)

    print(
        "Environments found: "
        + ", ".join(
            sorted(environments.keys())
        )
    )

    print_signature_summary(
        environments
    )

    plot_packet_loss(
        environments
    )

    plot_delay(
        environments
    )

    plot_throughput(
        environments
    )

    print()
    print("========================================")
    print("      SIGNATURE ANALYSIS COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
