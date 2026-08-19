import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHPROBE-AI
# FINAL MULTI-RUN BENCHMARK
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")
NS3_DIR = Path("/home/harsha/ns-3.48")

AGENT = PROJECT_DIR / "agent" / "autonomous_investigator.py"

RESULTS_DIR = PROJECT_DIR / "dataset" / "results"

CSV_FILE = RESULTS_DIR / "final_benchmark.csv"
JSON_FILE = RESULTS_DIR / "final_benchmark_summary.json"


# Number of repetitions for each environment
RUNS_PER_ENVIRONMENT = 3

ENVIRONMENTS = {
    "E0": {
        "choice": "1",
        "name": "NORMAL",
    },
    "E1": {
        "choice": "2",
        "name": "RATE_LIMITED",
    },
    "E2": {
        "choice": "3",
        "name": "DELAY",
    },
}


# ============================================================
# RUN AGENT
# ============================================================

def run_agent(environment_id):

    choice = ENVIRONMENTS[environment_id]["choice"]

    command = [
        "python3",
        str(AGENT),
    ]

    result = subprocess.run(
        command,
        input=f"{choice}\n",
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )

    if result.returncode != 0:

        print(result.stdout)
        print(result.stderr)

        raise RuntimeError(
            f"Agent failed for {environment_id}"
        )

    output = result.stdout

    return output


# ============================================================
# PARSE AGENT OUTPUT
# ============================================================

def parse_result(output):

    diagnosis = None
    confidence = None
    probes = None

    # Final diagnosis
    for line in output.splitlines():

        line = line.strip()

        if line.startswith(
            ">>> FINAL DIAGNOSIS:"
        ):

            diagnosis = line.split(
                ":", 1
            )[1].strip()

        elif line.startswith(
            ">>> CONFIDENCE:"
        ):

            try:

                confidence = float(
                    line.split(
                        ":", 1
                    )[1].strip()
                )

            except ValueError:

                confidence = None

    # Count actual agent steps
    probes = sum(
        1
        for line in output.splitlines()
        if line.startswith(
            "       PATHPROBE-AI AGENT STEP"
        )
    )

    if diagnosis is None:

        raise RuntimeError(
            "Could not parse final diagnosis."
        )

    if confidence is None:

        raise RuntimeError(
            "Could not parse confidence."
        )

    if probes is None or probes == 0:

        raise RuntimeError(
            "Could not determine probe count."
        )

    return diagnosis, confidence, probes


# ============================================================
# MAIN BENCHMARK
# ============================================================

def main():

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       FINAL BENCHMARK")
    print("========================================")

    print()
    print(
        f"Runs per environment : "
        f"{RUNS_PER_ENVIRONMENT}"
    )

    print(
        f"Total planned runs   : "
        f"{len(ENVIRONMENTS) * RUNS_PER_ENVIRONMENT}"
    )

    print(
        f"Maximum probes/run   : 4"
    )

    print("========================================")

    results = []

    for environment_id, info in ENVIRONMENTS.items():

        actual = info["name"]

        print()
        print(
            "========================================"
        )

        print(
            f"TESTING {environment_id} "
            f"({actual})"
        )

        print(
            "========================================"
        )

        for run_number in range(
            1,
            RUNS_PER_ENVIRONMENT + 1
        ):

            print()
            print(
                f"Run {run_number}/"
                f"{RUNS_PER_ENVIRONMENT}"
            )

            print(
                "----------------------------------------"
            )

            output = run_agent(
                environment_id
            )

            diagnosis, confidence, probes = (
                parse_result(output)
            )

            correct = (
                diagnosis == actual
            )

            reduction = (
                (4 - probes) / 4 * 100
            )

            print(
                f"Actual       : {actual}"
            )

            print(
                f"Diagnosis    : {diagnosis}"
            )

            print(
                f"Confidence   : "
                f"{confidence:.2f}"
            )

            print(
                f"Probes       : {probes}"
            )

            print(
                f"Probe saving : "
                f"{reduction:.2f}%"
            )

            print(
                f"Correct      : "
                f"{'YES' if correct else 'NO'}"
            )

            results.append(
                {
                    "timestamp":
                        datetime.now().isoformat(),

                    "environment":
                        environment_id,

                    "actual":
                        actual,

                    "run":
                        run_number,

                    "diagnosis":
                        diagnosis,

                    "confidence":
                        confidence,

                    "probes_used":
                        probes,

                    "fixed_probes":
                        4,

                    "probe_reduction_percent":
                        round(
                            reduction,
                            2
                        ),

                    "correct":
                        correct,
                }
            )

    # ========================================================
    # CALCULATE SUMMARY
    # ========================================================

    total_runs = len(results)

    correct_runs = sum(
        1
        for row in results
        if row["correct"]
    )

    accuracy = (
        correct_runs /
        total_runs *
        100
        if total_runs
        else 0
    )

    average_probes = (
        sum(
            row["probes_used"]
            for row in results
        )
        /
        total_runs
        if total_runs
        else 0
    )

    average_confidence = (
        sum(
            row["confidence"]
            for row in results
        )
        /
        total_runs
        if total_runs
        else 0
    )

    average_reduction = (
        sum(
            row[
                "probe_reduction_percent"
            ]
            for row in results
        )
        /
        total_runs
        if total_runs
        else 0
    )

    # --------------------------------------------------------
    # Per-environment statistics
    # --------------------------------------------------------

    environment_summary = {}

    for environment_id, info in ENVIRONMENTS.items():

        rows = [
            row
            for row in results
            if row["environment"]
            == environment_id
        ]

        env_correct = sum(
            1
            for row in rows
            if row["correct"]
        )

        env_accuracy = (
            env_correct /
            len(rows) *
            100
            if rows
            else 0
        )

        env_average_probes = (
            sum(
                row["probes_used"]
                for row in rows
            )
            /
            len(rows)
            if rows
            else 0
        )

        env_average_confidence = (
            sum(
                row["confidence"]
                for row in rows
            )
            /
            len(rows)
            if rows
            else 0
        )

        environment_summary[
            environment_id
        ] = {

            "name":
                info["name"],

            "runs":
                len(rows),

            "accuracy_percent":
                round(
                    env_accuracy,
                    2
                ),

            "average_probes":
                round(
                    env_average_probes,
                    2
                ),

            "average_confidence":
                round(
                    env_average_confidence,
                    3
                ),
        }

    # ========================================================
    # SAVE CSV
    # ========================================================

    fieldnames = [
        "timestamp",
        "environment",
        "actual",
        "run",
        "diagnosis",
        "confidence",
        "probes_used",
        "fixed_probes",
        "probe_reduction_percent",
        "correct",
    ]

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    # ========================================================
    # SAVE JSON SUMMARY
    # ========================================================

    summary = {

        "project":
            "PathProbe-AI",

        "benchmark":
            "final_multi_run_benchmark",

        "generated_at":
            datetime.now().isoformat(),

        "runs_per_environment":
            RUNS_PER_ENVIRONMENT,

        "total_runs":
            total_runs,

        "correct_runs":
            correct_runs,

        "overall_accuracy_percent":
            round(
                accuracy,
                2
            ),

        "average_adaptive_probes":
            round(
                average_probes,
                2
            ),

        "fixed_probes":
            4,

        "average_probe_reduction_percent":
            round(
                average_reduction,
                2
            ),

        "average_confidence":
            round(
                average_confidence,
                3
            ),

        "environment_results":
            environment_summary,

        "raw_results":
            results,
    }

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

    # ========================================================
    # FINAL DISPLAY
    # ========================================================

    print()
    print("========================================")
    print("       FINAL BENCHMARK RESULTS")
    print("========================================")

    print(
        f"Total Runs             : "
        f"{total_runs}"
    )

    print(
        f"Correct Runs           : "
        f"{correct_runs}"
    )

    print(
        f"Overall Accuracy       : "
        f"{accuracy:.2f}%"
    )

    print(
        f"Average Adaptive Probes: "
        f"{average_probes:.2f}"
    )

    print(
        f"Fixed Probes           : "
        f"4.00"
    )

    print(
        f"Average Probe Reduction:"
        f" {average_reduction:.2f}%"
    )

    print(
        f"Average Confidence     : "
        f"{average_confidence:.3f}"
    )

    print()
    print("Environment Results")
    print("----------------------------------------")

    for environment_id, data in (
        environment_summary.items()
    ):

        print(
            f"{environment_id} "
            f"({data['name']})"
        )

        print(
            f"  Accuracy          : "
            f"{data['accuracy_percent']:.2f}%"
        )

        print(
            f"  Average Probes    : "
            f"{data['average_probes']:.2f}"
        )

        print(
            f"  Average Confidence:"
            f" {data['average_confidence']:.3f}"
        )

    print()
    print("Saved:")
    print(
        f"CSV  : {CSV_FILE}"
    )
    print(
        f"JSON : {JSON_FILE}"
    )

    print()
    print("========================================")
    print("       BENCHMARK COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
