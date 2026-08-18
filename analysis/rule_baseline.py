import csv
from pathlib import Path


PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")

INPUT_FILE = (
    PROJECT_DIR
    / "dataset"
    / "processed"
    / "behavior_features.csv"
)


def diagnose(row):

    loss = float(
        row["max_packet_loss_percent"]
    )

    delay = float(
        row["delay_increase_ms"]
    )

    loss_onset = float(
        row["loss_onset_pps"]
    )

    if (
        loss >= 20
        and delay >= 100
    ):
        return (
            "RATE_LIMITED",
            0.90
        )

    if (
        loss > 0
        and delay >= 50
    ):
        return (
            "CONGESTION_OR_SHAPING",
            0.70
        )

    return (
        "NORMAL",
        0.80
    )


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    print()
    print("========================================")
    print("     PATHPROBE RULE BASELINE")
    print("========================================")
    print()

    for row in rows:

        diagnosis, confidence = diagnose(
            row
        )

        print(
            f"{row['environment_id']} "
            f"({row['environment_name']})"
        )

        print(
            f"Diagnosis : {diagnosis}"
        )

        print(
            f"Confidence: {confidence:.2f}"
        )

        print()


if __name__ == "__main__":
    main()
