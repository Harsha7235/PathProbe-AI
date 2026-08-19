import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHPROBE-AI
# ROBUSTNESS TEST
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")
AGENT = PROJECT_DIR / "agent" / "autonomous_investigator.py"

RESULTS_DIR = PROJECT_DIR / "dataset" / "results"

CSV_FILE = RESULTS_DIR / "robustness_results.csv"
JSON_FILE = RESULTS_DIR / "robustness_summary.json"

# Each environment is tested multiple times.
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

    result = subprocess.run(
        [
            "python3",
            str(AGENT),
        ],
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

    return result.stdout


# ============================================================
# PARSE FINAL RESULT
# ============================================================

def parse_result(output):

    diagnosis = None
    confidence = None

    for line in output.splitlines():

        line = line.strip()

        if line.startswith(
            ">>> FINAL DIAGNOSIS:"
        ):

            diagnosis = line.split(
                ":",
                1
            )[1].strip()

        elif line.startswith(
            ">>> CONFIDENCE:"
        ):

            try:

                confidence = float(
                    line.split(
                        ":",
                        1
                    )[1].strip()
                )

            except ValueError:

                confidence = None

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

    if probes == 0:
        raise RuntimeError(
            "Could not determine probe count."
        )

    return diagnosis, confidence, probes


# ============================================================
# ROBUSTNESS CATEGORY
# ============================================================

def classify_robustness(diagnosis, actual):

    if diagnosis == actual:
        return "PASS"

    return "FAIL"


# ============================================================
# MAIN
# ============================================================

def main():

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       ROBUSTNESS TEST")
    print("========================================")

    print()
    print(
        "Purpose:"
    )

    print(
        "Verify that autonomous diagnosis remains "
        "stable across repeated independent runs."
    )

    print()
    print(
        f"Runs per environment : "
        f"{RUNS_PER_ENVIRONMENT}"
    )

    print(
        f"Total planned runs   : "
        f"{len(ENVIRONMENTS) * RUNS_PER_ENVIRONMENT}"
    )

    print("========================================")

    results = []

    for environment_id, info in ENVIRONMENTS.items():

        actual = info["name"]

        print()
        print("========================================")
        print(
            f"TESTING {environment_id} "
            f"({actual})"
        )
        print("========================================")

        for run_number in range(
            1,
            RUNS_PER_ENVIRONMENT + 1
        ):

            print()
            print(
                f"Run {run_number}/"
                f"{RUNS_PER_ENVIRONMENT}"
            )

            output = run_agent(
                environment_id
            )

            diagnosis, confidence, probes = (
                parse_result(output)
            )

            result = classify_robustness(
                diagnosis,
                actual
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
                f"Robustness   : {result}"
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

                    "result":
                        result,
                }
            )

    # ========================================================
    # OVERALL METRICS
    # ========================================================

    total_runs = len(results)

    passed = sum(
        1
        for row in results
        if row["result"] == "PASS"
    )

    failed = (
        total_runs - passed
    )

    robustness_accuracy = (
        passed /
        total_runs *
        100
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

    # ========================================================
    # PER ENVIRONMENT
    # ========================================================

    environment_summary = {}

    for environment_id, info in ENVIRONMENTS.items():

        rows = [
            row
            for row in results
            if row["environment"]
            == environment_id
        ]

        env_passed = sum(
            1
            for row in rows
            if row["result"] == "PASS"
        )

        env_accuracy = (
            env_passed /
            len(rows) *
            100
            if rows
            else 0
        )

        env_confidence = (
            sum(
                row["confidence"]
                for row in rows
            )
            /
            len(rows)
            if rows
            else 0
        )

        env_probes = (
            sum(
                row["probes_used"]
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

            "passed":
                env_passed,

            "failed":
                len(rows) - env_passed,

            "accuracy_percent":
                round(
                    env_accuracy,
                    2
                ),

            "average_confidence":
                round(
                    env_confidence,
                    3
                ),

            "average_probes":
                round(
                    env_probes,
                    2
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
        "result",
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
    # SAVE JSON
    # ========================================================

    summary = {

        "project":
            "PathProbe-AI",

        "test":
            "robustness_test",

        "generated_at":
            datetime.now().isoformat(),

        "runs_per_environment":
            RUNS_PER_ENVIRONMENT,

        "total_runs":
            total_runs,

        "passed_runs":
            passed,

        "failed_runs":
            failed,

        "robustness_accuracy_percent":
            round(
                robustness_accuracy,
                2
            ),

        "average_confidence":
            round(
                average_confidence,
                3
            ),

        "average_probes":
            round(
                average_probes,
                2
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
    # FINAL OUTPUT
    # ========================================================

    print()
    print("========================================")
    print("       ROBUSTNESS RESULTS")
    print("========================================")

    print(
        f"Total Runs          : "
        f"{total_runs}"
    )

    print(
        f"Passed Runs         : "
        f"{passed}"
    )

    print(
        f"Failed Runs         : "
        f"{failed}"
    )

    print(
        f"Robustness Accuracy : "
        f"{robustness_accuracy:.2f}%"
    )

    print(
        f"Average Confidence  : "
        f"{average_confidence:.3f}"
    )

    print(
        f"Average Probes      : "
        f"{average_probes:.2f}"
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
            f"  Accuracy       : "
            f"{data['accuracy_percent']:.2f}%"
        )

        print(
            f"  Passed         : "
            f"{data['passed']}"
        )

        print(
            f"  Failed         : "
            f"{data['failed']}"
        )

        print(
            f"  Avg Confidence:"
            f" {data['average_confidence']:.3f}"
        )

        print(
            f"  Avg Probes     : "
            f"{data['average_probes']:.2f}"
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
    print("       ROBUSTNESS TEST COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
