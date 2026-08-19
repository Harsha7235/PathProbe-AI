import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path("/mnt/c/Projects/PathProbe-AI")

REPORT_DIR = BASE_DIR / "reports" / "generated"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def create_report(
    environment,
    history,
    final_decision
):
    """
    Create a complete investigation report.

    The environment value is used only by the
    evaluation harness/report layer.

    It is NOT included in the Qwen prompt.
    """

    observations = [
        item["observation"]
        for item in history
    ]

    steps = []

    for index, item in enumerate(
        history,
        start=1
    ):

        observation = item["observation"]
        decision = item["decision"]

        steps.append({

            "step": index,

            "probe_rate_pps":
                observation["probe_rate_pps"],

            "packet_loss_percent":
                observation[
                    "packet_loss_percent"
                ],

            "average_delay_ms":
                observation[
                    "average_delay_ms"
                ],

            "throughput_mbps":
                observation[
                    "throughput_mbps"
                ],

            "packets_sent":
                observation[
                    "packets_sent"
                ],

            "packets_received":
                observation[
                    "packets_received"
                ],

            "hypothesis":
                decision.get(
                    "hypothesis"
                ),

            "confidence":
                decision.get(
                    "confidence"
                ),

            "reasoning":
                decision.get(
                    "reasoning"
                ),

            "evidence":
                decision.get(
                    "evidence",
                    []
                ),

            "next_probe_rate_pps":
                decision.get(
                    "next_probe_rate_pps"
                ),

            "stop":
                decision.get(
                    "stop",
                    False
                )
        })

    probe_count = len(
        observations
    )

    maximum_probe_budget = 4

    probe_reduction = (
        (
            maximum_probe_budget
            - probe_count
        )
        / maximum_probe_budget
        * 100
    )

    report = {

        "project":
            "PathProbe-AI",

        "report_type":
            "autonomous_network_investigation",

        "generated_at":
            datetime.now().isoformat(),

        "evaluation_environment":
            environment,

        "environment_hidden_from_llm":
            True,

        "final_diagnosis":
            final_decision.get(
                "hypothesis"
            ),

        "final_confidence":
            final_decision.get(
                "confidence"
            ),

        "probes_used":
            probe_count,

        "maximum_probe_budget":
            maximum_probe_budget,

        "probe_reduction_percent":
            round(
                probe_reduction,
                2
            ),

        "investigation_steps":
            steps,

        "observations":
            observations
    }

    return report


def save_json(report):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = (
        REPORT_DIR
        / f"investigation_{timestamp}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2
        )

    return path


def save_markdown(report):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = (
        REPORT_DIR
        / f"investigation_{timestamp}.md"
    )

    lines = []

    lines.append(
        "# PATHPROBE-AI INVESTIGATION REPORT"
    )

    lines.append("")

    lines.append(
        f"Generated: {report['generated_at']}"
    )

    lines.append("")

    lines.append(
        "## Final Diagnosis"
    )

    lines.append("")

    lines.append(
        f"**Diagnosis:** "
        f"{report['final_diagnosis']}"
    )

    lines.append("")

    lines.append(
        f"**Confidence:** "
        f"{float(report['final_confidence']) * 100:.1f}%"
    )

    lines.append("")

    lines.append(
        "## Investigation Efficiency"
    )

    lines.append("")

    lines.append(
        f"- Probes used: "
        f"{report['probes_used']}"
    )

    lines.append(
        f"- Maximum probe budget: "
        f"{report['maximum_probe_budget']}"
    )

    lines.append(
        f"- Probe reduction: "
        f"{report['probe_reduction_percent']:.2f}%"
    )

    lines.append("")

    lines.append(
        "## Investigation Timeline"
    )

    lines.append("")

    for step in report[
        "investigation_steps"
    ]:

        lines.append(
            f"### Step {step['step']}"
        )

        lines.append("")

        lines.append(
            f"- Probe rate: "
            f"{step['probe_rate_pps']} pps"
        )

        lines.append(
            f"- Packet loss: "
            f"{step['packet_loss_percent']:.2f}%"
        )

        lines.append(
            f"- Average delay: "
            f"{step['average_delay_ms']:.2f} ms"
        )

        lines.append(
            f"- Throughput: "
            f"{step['throughput_mbps']:.6f} Mbps"
        )

        lines.append(
            f"- Packets: "
            f"{step['packets_received']}/"
            f"{step['packets_sent']}"
        )

        lines.append(
            f"- Hypothesis: "
            f"{step['hypothesis']}"
        )

        lines.append(
            f"- Confidence: "
            f"{float(step['confidence']) * 100:.1f}%"
        )

        lines.append("")

        lines.append(
            "**Reasoning:**"
        )

        lines.append("")

        lines.append(
            step["reasoning"] or
            "No reasoning supplied."
        )

        lines.append("")

        lines.append(
            "**Evidence:**"
        )

        lines.append("")

        evidence = step.get(
            "evidence",
            []
        )

        if evidence:

            for item in evidence:

                lines.append(
                    f"- {item}"
                )

        else:

            lines.append(
                "- No explicit evidence recorded."
            )

        lines.append("")

        lines.append(
            f"- Next probe: "
            f"{step['next_probe_rate_pps']}"
        )

        lines.append(
            f"- Stop: "
            f"{step['stop']}"
        )

        lines.append("")

    lines.append(
        "## Reproducibility"
    )

    lines.append("")

    lines.append(
        "The investigation was performed using "
        "the PathProbe-AI autonomous probing loop "
        "and ns-3 simulation measurements."
    )

    lines.append("")

    lines.append(
        "The hidden environment label was kept "
        "outside the Qwen reasoning prompt."
    )

    lines.append("")

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(lines)
        )

    return path


def generate_report(
    environment,
    history,
    final_decision
):

    report = create_report(
        environment,
        history,
        final_decision
    )

    json_path = save_json(
        report
    )

    markdown_path = save_markdown(
        report
    )

    print()
    print(
        "========================================"
    )

    print(
        "   INVESTIGATION REPORT GENERATED"
    )

    print(
        "========================================"
    )

    print(
        f"JSON     : {json_path}"
    )

    print(
        f"Markdown : {markdown_path}"
    )

    print(
        "========================================"
    )

    return report


if __name__ == "__main__":

    print(
        "This module is imported by "
        "autonomous_investigator.py."
    )
