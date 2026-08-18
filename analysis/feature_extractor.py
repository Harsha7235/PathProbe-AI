import csv
from pathlib import Path


PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")

INPUT_FILE = (
    PROJECT_DIR
    / "dataset"
    / "raw"
    / "environment_observations.csv"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "dataset"
    / "processed"
    / "behavior_features.csv"
)


def load_data():
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def to_float(row, key):
    return float(row[key])


def extract_environment_features(rows):

    rows = sorted(
        rows,
        key=lambda x: float(x["probe_value"])
    )

    loss_values = [
        to_float(r, "packet_loss_percent")
        for r in rows
    ]

    delay_values = [
        to_float(r, "average_delay_ms")
        for r in rows
    ]

    throughput_values = [
        to_float(r, "throughput_mbps")
        for r in rows
    ]

    rate_values = [
        to_float(r, "probe_value")
        for r in rows
    ]

    # --------------------------------------------------------
    # LOSS ONSET
    # --------------------------------------------------------

    loss_onset = None

    for row in rows:
        loss = to_float(
            row,
            "packet_loss_percent"
        )

        if loss > 0:
            loss_onset = float(
                row["probe_value"]
            )
            break

    # --------------------------------------------------------
    # MAX LOSS
    # --------------------------------------------------------

    max_loss = max(loss_values)

    # --------------------------------------------------------
    # DELAY CHANGE
    # --------------------------------------------------------

    baseline_delay = delay_values[0]
    maximum_delay = max(delay_values)

    delay_increase = (
        maximum_delay -
        baseline_delay
    )

    # --------------------------------------------------------
    # THROUGHPUT
    # --------------------------------------------------------

    maximum_throughput = max(
        throughput_values
    )

    # --------------------------------------------------------
    # THROUGHPUT GROWTH
    # --------------------------------------------------------

    first_throughput = throughput_values[0]

    if first_throughput > 0:
        throughput_growth = (
            maximum_throughput /
            first_throughput
        )
    else:
        throughput_growth = 0.0

    # --------------------------------------------------------
    # CONGESTION / SATURATION INDICATOR
    # --------------------------------------------------------

    saturation_indicator = 0.0

    for i in range(1, len(rows)):

        previous_rate = rate_values[i - 1]
        current_rate = rate_values[i]

        previous_tp = throughput_values[i - 1]
        current_tp = throughput_values[i]

        rate_change = (
            current_rate -
            previous_rate
        )

        tp_change = (
            current_tp -
            previous_tp
        )

        if rate_change > 0:

            ratio = (
                tp_change /
                rate_change
            )

            if ratio < saturation_indicator:
                saturation_indicator = ratio

    # --------------------------------------------------------
    # BEHAVIOR FLAGS
    # --------------------------------------------------------

    loss_detected = (
        max_loss > 0
    )

    severe_delay = (
        delay_increase >= 100
    )

    severe_loss = (
        max_loss >= 20
    )

    return {
        "environment_id":
            rows[0]["environment_id"],

        "environment_name":
            rows[0]["environment_name"],

        "max_packet_loss_percent":
            round(max_loss, 4),

        "loss_onset_pps":
            loss_onset
            if loss_onset is not None
            else -1,

        "baseline_delay_ms":
            round(baseline_delay, 4),

        "maximum_delay_ms":
            round(maximum_delay, 4),

        "delay_increase_ms":
            round(delay_increase, 4),

        "maximum_throughput_mbps":
            round(maximum_throughput, 6),

        "throughput_growth_factor":
            round(throughput_growth, 4),

        "loss_detected":
            int(loss_detected),

        "severe_loss":
            int(severe_loss),

        "severe_delay":
            int(severe_delay)
    }


def main():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_FILE}"
        )

    rows = load_data()

    environments = {}

    for row in rows:

        environment_id = row[
            "environment_id"
        ]

        environments.setdefault(
            environment_id,
            []
        ).append(row)

    features = []

    for environment_id, environment_rows in environments.items():

        result = extract_environment_features(
            environment_rows
        )

        features.append(result)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "environment_id",
        "environment_name",
        "max_packet_loss_percent",
        "loss_onset_pps",
        "baseline_delay_ms",
        "maximum_delay_ms",
        "delay_increase_ms",
        "maximum_throughput_mbps",
        "throughput_growth_factor",
        "loss_detected",
        "severe_loss",
        "severe_delay"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(features)

    print()
    print("========================================")
    print("      PATHPROBE FEATURE EXTRACTION")
    print("========================================")
    print()

    for feature in features:

        print(
            f"{feature['environment_id']} | "
            f"Loss: "
            f"{feature['max_packet_loss_percent']}% | "
            f"Loss onset: "
            f"{feature['loss_onset_pps']} pps | "
            f"Delay increase: "
            f"{feature['delay_increase_ms']} ms"
        )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
