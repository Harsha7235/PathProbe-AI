import subprocess
import re
from pathlib import Path
from collections import defaultdict


NS3_DIR = Path("/home/harsha/ns-3.48")

EXECUTABLES = {
    "E0": NS3_DIR / "build/scratch/ns3.48-pathprobe_rate-default",
    "E1": NS3_DIR / "build/scratch/ns3.48-pathprobe_rate_limited-default",
    "E2": NS3_DIR / "build/scratch/ns3.48-pathprobe_delay_jitter-default",
}

RATES = [50, 100, 200, 500]


def run_probe(environment, rate):

    command = [
        str(EXECUTABLES[environment]),
        f"--packetsPerSecond={rate}"
    ]

    if environment == "E1":
        command.append("--rateLimit=1Mbps")

    result = subprocess.run(
        command,
        cwd=NS3_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    output = result.stdout

    loss = float(
        re.search(
            r"Packet Loss\s*:\s*([\d.]+)",
            output
        ).group(1)
    )

    delay = float(
        re.search(
            r"Average Delay\s*:\s*([\d.]+)",
            output
        ).group(1)
    )

    throughput = float(
        re.search(
            r"Throughput\s*:\s*([\d.]+)",
            output
        ).group(1)
    )

    return {
        "rate": rate,
        "loss": loss,
        "delay": delay,
        "throughput": throughput,
    }


def classify(observations):

    # Strong rate-limiting signature.
    for obs in observations:

        if (
            obs["loss"] >= 20
            and obs["delay"] >= 100
        ):
            return "E1"

    # Persistent high delay with little/no loss.
    delays = [
        obs["delay"]
        for obs in observations
    ]

    losses = [
        obs["loss"]
        for obs in observations
    ]

    if (
        len(delays) > 0
        and sum(delays) / len(delays) >= 70
        and max(losses) < 5
    ):
        return "E2"

    return "E0"


def adaptive_probe(environment):

    observations = []

    # Start with inexpensive probe.
    rate = 50

    while True:

        result = run_probe(
            environment,
            rate
        )

        observations.append(result)

        # --------------------------------------------
        # RATE-LIMITED DETECTION
        # --------------------------------------------

        if (
            result["loss"] >= 20
            and result["delay"] >= 100
        ):
            break

        # --------------------------------------------
        # DELAY DETECTION
        # --------------------------------------------

        if (
            result["delay"] >= 70
            and result["loss"] < 5
        ):
            break

        # --------------------------------------------
        # MOVE TO NEXT PROBE
        # --------------------------------------------

        if rate == 50:
            rate = 100

        elif rate == 100:
            rate = 200

        elif rate == 200:
            rate = 500

        else:
            break

    return observations


def fixed_probe(environment):

    observations = []

    for rate in RATES:

        observations.append(
            run_probe(
                environment,
                rate
            )
        )

    return observations


def print_run(
    strategy,
    actual,
    predicted,
    observations
):

    print()
    print("----------------------------------------")
    print(f"Strategy   : {strategy}")
    print(f"Actual     : {actual}")
    print(f"Predicted  : {predicted}")
    print(
        f"Probes     : {len(observations)}"
    )

    for obs in observations:

        print(
            f"{obs['rate']:4} pps | "
            f"Loss {obs['loss']:6.2f}% | "
            f"Delay {obs['delay']:7.2f} ms | "
            f"TP {obs['throughput']:8.4f} Mbps"
        )


def main():

    environments = ["E0", "E1", "E2"]

    confusion = defaultdict(int)

    adaptive_probe_counts = []
    fixed_probe_counts = []

    correct = 0
    total = 0

    print()
    print("========================================")
    print("   PATHPROBE-AI 3-CLASS EVALUATION")
    print("========================================")

    for environment in environments:

        print()
        print(
            f"========== TESTING {environment} =========="
        )

        # ==========================================
        # ADAPTIVE
        # ==========================================

        adaptive = adaptive_probe(
            environment
        )

        adaptive_prediction = classify(
            adaptive
        )

        adaptive_probe_counts.append(
            len(adaptive)
        )

        print_run(
            "ADAPTIVE",
            environment,
            adaptive_prediction,
            adaptive
        )

        confusion[
            (environment, adaptive_prediction)
        ] += 1

        total += 1

        if adaptive_prediction == environment:
            correct += 1

        # ==========================================
        # FIXED
        # ==========================================

        fixed = fixed_probe(
            environment
        )

        fixed_prediction = classify(
            fixed
        )

        fixed_probe_counts.append(
            len(fixed)
        )

        print_run(
            "FIXED",
            environment,
            fixed_prediction,
            fixed
        )

    # ======================================================
    # SUMMARY
    # ======================================================

    accuracy = (
        correct / total * 100
        if total
        else 0
    )

    average_adaptive = (
        sum(adaptive_probe_counts)
        / len(adaptive_probe_counts)
    )

    average_fixed = (
        sum(fixed_probe_counts)
        / len(fixed_probe_counts)
    )

    reduction = (
        (average_fixed - average_adaptive)
        / average_fixed
        * 100
    )

    print()
    print("========================================")
    print("          FINAL EVALUATION")
    print("========================================")

    print(
        f"Accuracy              : "
        f"{accuracy:.2f}%"
    )

    print(
        f"Average adaptive probes: "
        f"{average_adaptive:.2f}"
    )

    print(
        f"Average fixed probes   : "
        f"{average_fixed:.2f}"
    )

    print(
        f"Probe reduction        : "
        f"{reduction:.2f}%"
    )

    print()
    print("CONFUSION MATRIX")
    print()

    print(
        "              Predicted"
    )

    print(
        "Actual       E0       E1       E2"
    )

    for actual in environments:

        values = []

        for predicted in environments:

            values.append(
                confusion[
                    (actual, predicted)
                ]
            )

        print(
            f"{actual:5}       "
            f"{values[0]:2}       "
            f"{values[1]:2}       "
            f"{values[2]:2}"
        )

    print()
    print("========================================")


if __name__ == "__main__":
    main()
