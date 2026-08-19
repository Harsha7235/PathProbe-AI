import csv
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_DIR = PROJECT_ROOT / "dataset" / "results"

RESULTS_FILE = RESULTS_DIR / "investigation_results.csv"


def save_investigation_result(
    environment,
    diagnosis,
    confidence,
    probes_used
):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = RESULTS_FILE.exists()

    fieldnames = [
        "timestamp",
        "environment",
        "diagnosis",
        "confidence",
        "probes_used",
        "probe_reduction_percent"
    ]

    probe_reduction = (
        (4 - probes_used) / 4
    ) * 100

    row = {
        "timestamp":
            datetime.now().isoformat(),

        "environment":
            environment,

        "diagnosis":
            diagnosis,

        "confidence":
            confidence,

        "probes_used":
            probes_used,

        "probe_reduction_percent":
            round(
                probe_reduction,
                2
            )
    }

    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:

            writer.writeheader()

        writer.writerow(row)

    print()
    print(
        f"Saved investigation result: "
        f"{RESULTS_FILE}"
    )


if __name__ == "__main__":

    print(
        "Investigation result logger ready."
    )

    print(
        f"Output: {RESULTS_FILE}"
    )
