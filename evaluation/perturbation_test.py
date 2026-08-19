import csv
import json
import random
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHPROBE-AI
# PERTURBATION / NOISE ROBUSTNESS TEST
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")

INPUT_FILE = (
    PROJECT_DIR
    / "dataset/raw/environment_observations.csv"
)

RESULTS_DIR = (
    PROJECT_DIR
    / "dataset/results"
)

CSV_FILE = (
    RESULTS_DIR
    / "perturbation_results.csv"
)

JSON_FILE = (
    RESULTS_DIR
    / "perturbation_summary.json"
)


# ============================================================
# TEST CONFIGURATION
# ============================================================

RANDOM_SEED = 42

# Percentage noise applied to measurements.
LOSS_NOISE = 0.05
DELAY_NOISE = 0.05
THROUGHPUT_NOISE = 0.05

# Keep the same probe rates as the real observations.
TEST_RATES = [50, 100, 200, 500]


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(observations):

    if not observations:
        return "UNCERTAIN"

    # Rate-limited signature:
    # loss + severe delay at higher load.
    for obs in observations:

        if (
            obs["probe_rate_pps"] >= 200
            and obs["packet_loss_percent"] > 5
            and obs["average_delay_ms"] >= 100
        ):
            return "RATE_LIMITED"

    # Delay signature:
    # persistent high delay with zero loss.
    high_delay = [
        obs
        for obs in observations
        if (
            obs["average_delay_ms"] >= 100
            and obs["packet_loss_percent"] <= 5
        )
    ]

    if len(high_delay) >= 2:

        delays = [
            obs["average_delay_ms"]
            for obs in high_delay
        ]

        if max(delays) - min(delays) <= 20:

            return "DELAY"

    # Normal signature:
    # high-rate probes still have low delay and low loss.
    high_rate = [
        obs
        for obs in observations
        if obs["probe_rate_pps"] >= 200
    ]

    if high_rate:

        if all(
            obs["packet_loss_percent"] <= 5
            and obs["average_delay_ms"] < 50
            for obs in high_rate
        ):
            return "NORMAL"

    return "UNCERTAIN"


# ============================================================
# APPLY MEASUREMENT NOISE
# ============================================================

def perturb(value, noise):

    factor = random.uniform(
        1.0 - noise,
        1.0 + noise
    )

    return value * factor


def perturb_observation(row):

    loss = float(
        row["packet_loss_percent"]
    )

    delay = float(
        row["average_delay_ms"]
    )

    throughput = float(
        row["throughput_mbps"]
    )

    # Loss should never become negative.
    loss = max(
        0.0,
        perturb(
            loss,
            LOSS_NOISE
        )
    )

    delay = max(
        0.0,
        perturb(
            delay,
            DELAY_NOISE
        )
    )

    throughput = max(
        0.0,
        perturb(
            throughput,
            THROUGHPUT_NOISE
        )
    )

    return {
        "environment":
            row["environment_id"],

        "environment_name":
            row["environment_name"].upper(),

        "probe_rate_pps":
            int(row["probe_value"]),

        "packet_loss_percent":
            loss,

        "average_delay_ms":
            delay,

        "throughput_mbps":
            throughput,
    }


# ============================================================
# LOAD DATA
# ============================================================

def load_observations():

    environments = {}

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            environment = row[
                "environment_id"
            ]

            observation = perturb_observation(
                row
            )

            environments.setdefault(
                environment,
                []
            ).append(
                observation
            )

    for environment in environments:

        environments[environment].sort(
            key=lambda x:
            x["probe_rate_pps"]
        )

    return environments


# ============================================================
# MAIN
# ============================================================

def main():

    random.seed(
        RANDOM_SEED
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       PERTURBATION TEST")
    print("========================================")

    print()
    print(
        "Measurement noise:"
    )

    print(
        f"  Loss       : ±{LOSS_NOISE * 100:.1f}%"
    )

    print(
        f"  Delay      : ±{DELAY_NOISE * 100:.1f}%"
    )

    print(
        f"  Throughput : ±{THROUGHPUT_NOISE * 100:.1f}%"
    )

    print(
        f"Random seed : {RANDOM_SEED}"
    )

    print("========================================")

    environments = load_observations()

    results = []

    for environment_id, observations in (
        environments.items()
    ):

        actual_map = {
            "E0": "NORMAL",
            "E1": "RATE_LIMITED",
            "E2": "DELAY",
        }

        actual = actual_map[
            environment_id
        ]

        diagnosis = classify(
            observations
        )

        passed = (
            diagnosis == actual
        )

        print()
        print("----------------------------------------")
        print(
            f"{environment_id} | "
            f"Actual: {actual}"
        )

        for obs in observations:

            print(
                f"{obs['probe_rate_pps']:4d} pps | "
                f"Loss {obs['packet_loss_percent']:7.2f}% | "
                f"Delay {obs['average_delay_ms']:7.2f} ms | "
                f"TP {obs['throughput_mbps']:7.4f} Mbps"
            )

        print(
            f"Diagnosis: {diagnosis}"
        )

        print(
            f"Result   : "
            f"{'PASS' if passed else 'FAIL'}"
        )

        results.append(
            {
                "timestamp":
                    datetime.now().isoformat(),

                "environment":
                    environment_id,

                "actual":
                    actual,

                "diagnosis":
                    diagnosis,

                "result":
                    "PASS"
                    if passed
                    else "FAIL",
            }
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(results)

    passed = sum(
        1
        for row in results
        if row["result"] == "PASS"
    )

    failed = total - passed

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    summary = {

        "project":
            "PathProbe-AI",

        "test":
            "measurement_perturbation",

        "generated_at":
            datetime.now().isoformat(),

        "random_seed":
            RANDOM_SEED,

        "loss_noise_percent":
            LOSS_NOISE * 100,

        "delay_noise_percent":
            DELAY_NOISE * 100,

        "throughput_noise_percent":
            THROUGHPUT_NOISE * 100,

        "total_environments":
            total,

        "passed":
            passed,

        "failed":
            failed,

        "accuracy_percent":
            round(
                accuracy,
                2
            ),

        "results":
            results,
    }

    # ========================================================
    # SAVE CSV
    # ========================================================

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp",
                "environment",
                "actual",
                "diagnosis",
                "result",
            ]
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    # ========================================================
    # SAVE JSON
    # ========================================================

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            indent=4
        )

    print()
    print("========================================")
    print("       FINAL PERTURBATION RESULTS")
    print("========================================")

    print(
        f"Environments : {total}"
    )

    print(
        f"Passed       : {passed}"
    )

    print(
        f"Failed       : {failed}"
    )

    print(
        f"Accuracy     : {accuracy:.2f}%"
    )

    print()
    print(
        f"CSV  : {CSV_FILE}"
    )

    print(
        f"JSON : {JSON_FILE}"
    )

    print()
    print("========================================")
    print("       PERTURBATION TEST COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
