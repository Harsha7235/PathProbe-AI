import csv
import json
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")
RESULTS_DIR = PROJECT_DIR / "dataset" / "results"

OUTPUT_JSON = RESULTS_DIR / "final_evaluation.json"
OUTPUT_MD = RESULTS_DIR / "FINAL_EVALUATION.md"


def load_csv(filename):
    path = RESULTS_DIR / filename

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def calculate_accuracy(rows, actual_field, predicted_field):
    if not rows:
        return 0.0

    correct = 0

    for row in rows:
        if row.get(actual_field) == row.get(predicted_field):
            correct += 1

    return correct / len(rows) * 100


def main():

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       FINAL PROJECT EVALUATION")
    print("========================================")

    # --------------------------------------------------
    # LOAD EXISTING RESULTS
    # --------------------------------------------------

    adaptive_rows = load_csv(
        "adaptive_vs_fixed.csv"
    )

    robustness_rows = load_csv(
        "robustness_results.csv"
    )

    perturbation_rows = load_csv(
        "perturbation_results.csv"
    )

    end_to_end_rows = load_csv(
        "end_to_end_results.csv"
    )

    # --------------------------------------------------
    # ADAPTIVE VS FIXED
    # --------------------------------------------------

    adaptive_accuracy = calculate_accuracy(
        adaptive_rows,
        "actual",
        "adaptive_diagnosis"
    )

    fixed_accuracy = calculate_accuracy(
        adaptive_rows,
        "actual",
        "fixed_diagnosis"
    )

    adaptive_avg_probes = 0.0
    fixed_avg_probes = 0.0
    probe_reduction = 0.0

    if adaptive_rows:

        adaptive_avg_probes = sum(
            int(row["adaptive_probes"])
            for row in adaptive_rows
        ) / len(adaptive_rows)

        fixed_avg_probes = sum(
            int(row["fixed_probes"])
            for row in adaptive_rows
        ) / len(adaptive_rows)

        if fixed_avg_probes > 0:

            probe_reduction = (
                1
                - adaptive_avg_probes / fixed_avg_probes
            ) * 100

    # --------------------------------------------------
    # ROBUSTNESS
    # --------------------------------------------------

    robustness_total = len(
        robustness_rows
    )

    robustness_passed = sum(
        1
        for row in robustness_rows
        if row.get("result", "").upper() == "PASS"
    )

    robustness_accuracy = 0.0

    if robustness_total > 0:
        robustness_accuracy = (
            robustness_passed
            / robustness_total
            * 100
        )

    # --------------------------------------------------
    # PERTURBATION
    # --------------------------------------------------

    perturbation_total = len(
        perturbation_rows
    )

    perturbation_passed = sum(
        1
        for row in perturbation_rows
        if row.get("result", "").upper() == "PASS"
    )

    perturbation_accuracy = 0.0

    if perturbation_total > 0:
        perturbation_accuracy = (
            perturbation_passed
            / perturbation_total
            * 100
        )

    # --------------------------------------------------
    # END-TO-END
    # --------------------------------------------------

    end_to_end_total = len(
        end_to_end_rows
    )

    end_to_end_passed = sum(
        1
        for row in end_to_end_rows
        if row.get("correct", "").lower()
        in ("true", "1", "yes", "pass")
    )

    end_to_end_accuracy = 0.0

    if end_to_end_total > 0:
        end_to_end_accuracy = (
            end_to_end_passed
            / end_to_end_total
            * 100
        )

    # --------------------------------------------------
    # OVERALL SCORE
    # --------------------------------------------------

    scores = []

    if adaptive_rows:
        scores.append(adaptive_accuracy)

    if robustness_rows:
        scores.append(robustness_accuracy)

    if perturbation_rows:
        scores.append(perturbation_accuracy)

    if end_to_end_rows:
        scores.append(end_to_end_accuracy)

    if scores:
        overall_accuracy = (
            sum(scores) / len(scores)
        )
    else:
        overall_accuracy = 0.0

    generated_at = datetime.now().isoformat()

    # --------------------------------------------------
    # JSON RESULT
    # --------------------------------------------------

    result = {
        "project": "PathProbe-AI",
        "evaluation_type": "final_project_evaluation",
        "generated_at": generated_at,

        "adaptive_vs_fixed": {
            "adaptive_accuracy_percent":
                round(adaptive_accuracy, 2),

            "fixed_accuracy_percent":
                round(fixed_accuracy, 2),

            "adaptive_average_probes":
                round(adaptive_avg_probes, 2),

            "fixed_average_probes":
                round(fixed_avg_probes, 2),

            "probe_reduction_percent":
                round(probe_reduction, 2)
        },

        "robustness": {
            "total_runs":
                robustness_total,

            "passed_runs":
                robustness_passed,

            "accuracy_percent":
                round(robustness_accuracy, 2)
        },

        "perturbation": {
            "total_tests":
                perturbation_total,

            "passed_tests":
                perturbation_passed,

            "accuracy_percent":
                round(perturbation_accuracy, 2)
        },

        "end_to_end": {
            "total_tests":
                end_to_end_total,

            "passed_tests":
                end_to_end_passed,

            "accuracy_percent":
                round(end_to_end_accuracy, 2)
        },

        "overall_accuracy_percent":
            round(overall_accuracy, 2)
    }

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    # --------------------------------------------------
    # MARKDOWN REPORT
    #
    # IMPORTANT:
    # No triple quoted string is used here.
    # --------------------------------------------------

    lines = []

    lines.append("# PATHPROBE-AI")
    lines.append("")
    lines.append("## Final Project Evaluation")
    lines.append("")
    lines.append(
        "Generated: " + generated_at
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. Project Objective")
    lines.append("")
    lines.append(
        "PathProbe-AI is an autonomous network-path "
        "diagnosis system combining:"
    )
    lines.append("")
    lines.append("- ns-3 network simulation")
    lines.append("- active network probing")
    lines.append("- deterministic evidence analysis")
    lines.append("- grounded Qwen LLM reasoning")
    lines.append("- adaptive probe selection")
    lines.append("- autonomous investigation")
    lines.append("- robustness evaluation")
    lines.append("- persistent experiment reporting")
    lines.append("")

    lines.append("The system diagnoses three hidden network behaviors:")
    lines.append("")
    lines.append("1. NORMAL")
    lines.append("2. RATE_LIMITED")
    lines.append("3. DELAY")
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 2. System Pipeline")
    lines.append("")
    lines.append("```text")
    lines.append("Hidden ns-3 Environment")
    lines.append("        |")
    lines.append("        v")
    lines.append("Active Network Probe")
    lines.append("        |")
    lines.append("        v")
    lines.append("Packet Loss / Delay / Throughput")
    lines.append("        |")
    lines.append("        v")
    lines.append("Deterministic Evidence Engine")
    lines.append("        |")
    lines.append("        v")
    lines.append("Grounded Qwen Reasoning")
    lines.append("        |")
    lines.append("        v")
    lines.append("Adaptive Probe Selection")
    lines.append("        |")
    lines.append("        v")
    lines.append("Autonomous Diagnosis")
    lines.append("        |")
    lines.append("        v")
    lines.append("Investigation Report")
    lines.append("        |")
    lines.append("        v")
    lines.append("Evaluation")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 3. Adaptive vs Fixed Evaluation")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|---|---:|")
    lines.append(
        f"| Adaptive Accuracy | {adaptive_accuracy:.2f}% |"
    )
    lines.append(
        f"| Fixed Accuracy | {fixed_accuracy:.2f}% |"
    )
    lines.append(
        f"| Adaptive Average Probes | {adaptive_avg_probes:.2f} |"
    )
    lines.append(
        f"| Fixed Average Probes | {fixed_avg_probes:.2f} |"
    )
    lines.append(
        f"| Probe Reduction | {probe_reduction:.2f}% |"
    )
    lines.append("")

    lines.append(
        "The adaptive agent maintains diagnosis accuracy "
        "while reducing the number of required probes."
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 4. Robustness Evaluation")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|---|---:|")
    lines.append(
        f"| Total Runs | {robustness_total} |"
    )
    lines.append(
        f"| Passed Runs | {robustness_passed} |"
    )
    lines.append(
        f"| Robustness Accuracy | {robustness_accuracy:.2f}% |"
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 5. Perturbation Evaluation")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|---|---:|")
    lines.append(
        f"| Total Tests | {perturbation_total} |"
    )
    lines.append(
        f"| Passed Tests | {perturbation_passed} |"
    )
    lines.append(
        f"| Perturbation Accuracy | {perturbation_accuracy:.2f}% |"
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 6. End-to-End Evaluation")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|---|---:|")
    lines.append(
        f"| Total Tests | {end_to_end_total} |"
    )
    lines.append(
        f"| Passed Tests | {end_to_end_passed} |"
    )
    lines.append(
        f"| End-to-End Accuracy | {end_to_end_accuracy:.2f}% |"
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 7. Overall Evaluation")
    lines.append("")
    lines.append(
        f"**Overall evaluation accuracy: "
        f"{overall_accuracy:.2f}%**"
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 8. Network Signatures")
    lines.append("")

    lines.append("### NORMAL")
    lines.append("")
    lines.append("- Low delay")
    lines.append("- Zero packet loss")
    lines.append("- Throughput increases with offered load")
    lines.append("- No congestion signature")
    lines.append("")

    lines.append("### RATE_LIMITED")
    lines.append("")
    lines.append("- Initially normal behavior")
    lines.append("- Increasing load produces packet loss")
    lines.append("- Delay increases sharply")
    lines.append("- Throughput approaches saturation")
    lines.append("")

    lines.append("### DELAY")
    lines.append("")
    lines.append("- Persistent high delay")
    lines.append("- Little or no packet loss")
    lines.append("- Delay remains high across probe rates")
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 9. Main Contribution")
    lines.append("")
    lines.append(
        "**black-box active probing + deterministic evidence "
        "+ grounded local LLM reasoning + autonomous probe selection**"
    )
    lines.append("")

    lines.append(
        "The hidden environment label is not provided to the LLM. "
        "The reasoning engine receives network measurements and "
        "determines the most likely network condition."
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 10. Limitations")
    lines.append("")
    lines.append(
        "The current evaluation uses three controlled ns-3 environments:"
    )
    lines.append("")
    lines.append("- E0 NORMAL")
    lines.append("- E1 RATE_LIMITED")
    lines.append("- E2 DELAY")
    lines.append("")

    lines.append(
        "Future work can include:"
    )
    lines.append("")
    lines.append("- additional failure classes")
    lines.append("- jitter")
    lines.append("- packet corruption")
    lines.append("- routing failures")
    lines.append("- wireless networks")
    lines.append("- real network traces")
    lines.append("- larger network topologies")
    lines.append("- additional LLMs")
    lines.append("- real-world deployment")
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 11. Conclusion")
    lines.append("")
    lines.append(
        "PathProbe-AI demonstrates a closed-loop autonomous "
        "network diagnosis workflow."
    )
    lines.append("")

    lines.append(
        "The system observes a network path, analyzes measured "
        "behavior, reasons about competing hypotheses, selects "
        "additional probes when necessary, and terminates when "
        "sufficient evidence supports a diagnosis."
    )
    lines.append("")

    lines.append(
        "The evaluation framework measures diagnosis accuracy, "
        "probing efficiency, robustness, perturbation tolerance, "
        "and complete end-to-end operation."
    )
    lines.append("")

    report = "\n".join(lines)

    with open(
        OUTPUT_MD,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(report)

    # --------------------------------------------------
    # DISPLAY
    # --------------------------------------------------

    print()
    print("========================================")
    print("       FINAL EVALUATION RESULTS")
    print("========================================")

    print(
        f"Adaptive Accuracy : "
        f"{adaptive_accuracy:.2f}%"
    )

    print(
        f"Fixed Accuracy    : "
        f"{fixed_accuracy:.2f}%"
    )

    print(
        f"Probe Reduction   : "
        f"{probe_reduction:.2f}%"
    )

    print(
        f"Robustness        : "
        f"{robustness_accuracy:.2f}%"
    )

    print(
        f"Perturbation      : "
        f"{perturbation_accuracy:.2f}%"
    )

    print(
        f"End-to-End        : "
        f"{end_to_end_accuracy:.2f}%"
    )

    print(
        f"Overall Accuracy  : "
        f"{overall_accuracy:.2f}%"
    )

    print()
    print(
        "JSON   : "
        + str(OUTPUT_JSON)
    )

    print(
        "REPORT : "
        + str(OUTPUT_MD)
    )

    print()
    print("========================================")
    print("       FINAL EVALUATION COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()
