import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHPROBE-AI
# END-TO-END EXPERIMENT RUNNER
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")

AGENT = PROJECT_DIR / "agent" / "autonomous_investigator.py"

RESULTS_DIR = PROJECT_DIR / "dataset" / "results"

CSV_FILE = RESULTS_DIR / "end_to_end_results.csv"
JSON_FILE = RESULTS_DIR / "end_to_end_summary.json"

ENVIRONMENTS = {
    "E0": "NORMAL",
    "E1": "RATE_LIMITED",
    "E2": "DELAY",
}


def run_agent(environment):

    choice = {
        "E0": "1",
        "E1": "2",
        "E2": "3",
    }[environment]

    result = subprocess.run(
        [sys.executable, str(AGENT)],
        input=choice + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_DIR,
    )

    if result.returncode != 0:

        print(result.stdout)
        print(result.stderr)

        raise RuntimeError(
            f"Agent failed for {environment}"
        )

    output = result.stdout

    diagnosis = "UNKNOWN"
    confidence = 0.0
    probes = 0

    # --------------------------------------------------------
    # Extract final diagnosis
    # --------------------------------------------------------

    for line in output.splitlines():

        line = line.strip()

        if line.startswith(
            ">>> FINAL DIAGNOSIS:"
        ):

            diagnosis = (
                line.split(
                    ":", 1
                )[1]
                .strip()
            )

        elif line.startswith(
            ">>> CONFIDENCE:"
        ):

            try:
                confidence = float(
                    line.split(
                        ":", 1
                    )[1]
                    .strip()
                )
            except ValueError:
                confidence = 0.0

    # --------------------------------------------------------
    # Count actual agent steps
    # --------------------------------------------------------

    probes = output.count(
        "PATHPROBE-AI AGENT STEP"
    )

    return {
        "environment": environment,
        "actual": ENVIRONMENTS[environment],
        "diagnosis": diagnosis,
        "confidence": confidence,
        "probes_used": probes,
        "correct": (
            diagnosis
            == ENVIRONMENTS[environment]
        ),
        "raw_output": output,
    }


def main():

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       END-TO-END EVALUATION")
    print("========================================")

    print()
    print(
        "Testing complete autonomous pipeline:"
    )

    print(
        "ns-3 → probing → evidence → Qwen → diagnosis"
    )

    print()
    print(
        f"Environments : {len(ENVIRONMENTS)}"
    )

    print("========================================")

    results = []

    for environment in ENVIRONMENTS:

        print()
        print(
            "========================================"
        )

        print(
            f"TESTING {environment} "
            f"({ENVIRONMENTS[environment]})"
        )

        print(
            "========================================"
        )

        result = run_agent(
            environment
        )

        results.append(result)

        print()
        print(
            f"Actual       : "
            f"{result['actual']}"
        )

        print(
            f"Diagnosis    : "
            f"{result['diagnosis']}"
        )

        print(
            f"Confidence   : "
            f"{result['confidence']:.2f}"
        )

        print(
            f"Probes       : "
            f"{result['probes_used']}"
        )

        print(
            f"Result       : "
            f"{'PASS' if result['correct'] else 'FAIL'}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["correct"]
    )

    failed = total - passed

    accuracy = (
        passed / total * 100
        if total
        else 0.0
    )

    average_confidence = (
        sum(
            result["confidence"]
            for result in results
        )
        / total
        if total
        else 0.0
    )

    average_probes = (
        sum(
            result["probes_used"]
            for result in results
        )
        / total
        if total
        else 0.0
    )

    summary = {

        "project":
            "PathProbe-AI",

        "experiment":
            "end_to_end_evaluation",

        "generated_at":
            datetime.now().isoformat(),

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

        "results": [
            {
                key: value
                for key, value in result.items()
                if key != "raw_output"
            }
            for result in results
        ],
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
                "confidence",
                "probes_used",
                "correct",
            ],
        )

        writer.writeheader()

        timestamp = datetime.now().isoformat()

        for result in results:

            writer.writerow({
                "timestamp":
                    timestamp,

                "environment":
                    result["environment"],

                "actual":
                    result["actual"],

                "diagnosis":
                    result["diagnosis"],

                "confidence":
                    result["confidence"],

                "probes_used":
                    result["probes_used"],

                "correct":
                    result["correct"],
            })

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

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("========================================")
    print("       FINAL END-TO-END RESULTS")
    print("========================================")

    print(
        f"Total Environments : {total}"
    )

    print(
        f"Passed             : {passed}"
    )

    print(
        f"Failed             : {failed}"
    )

    print(
        f"Accuracy           : {accuracy:.2f}%"
    )

    print(
        f"Average Confidence : "
        f"{average_confidence:.3f}"
    )

    print(
        f"Average Probes     : "
        f"{average_probes:.2f}"
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
    print("       END-TO-END TEST COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
