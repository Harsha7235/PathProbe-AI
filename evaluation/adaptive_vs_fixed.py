import subprocess
import re
from pathlib import Path


NS3_DIR = Path("/home/harsha/ns-3.48")

E0 = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_rate-default"
)

E1 = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_rate_limited-default"
)


RATES = [50, 100, 200, 500]


def run_probe(environment, rate):

    executable = E0 if environment == "E0" else E1

    command = [
        str(executable),
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
        raise RuntimeError(
            result.stderr
        )

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
        "throughput": throughput
    }


def fixed_strategy(environment):

    observations = []

    for rate in RATES:

        result = run_probe(
            environment,
            rate
        )

        observations.append(result)

    return observations


def adaptive_strategy(environment):

    observations = []

    # Start with a moderate probe.
    rate = 100

    while True:

        result = run_probe(
            environment,
            rate
        )

        observations.append(result)

        loss = result["loss"]
        delay = result["delay"]

        # Strong evidence of rate limiting.
        if loss >= 20 and delay >= 100:
            break

        # Normal behavior at 100 pps:
        # test the boundary.
        if rate == 100:
            rate = 200
            continue

        # If abnormal behavior appears,
        # diagnosis is sufficient.
        if loss > 0 or delay > 50:
            break

        # Otherwise perform stress test.
        if rate == 200:
            rate = 500
            continue

        break

    return observations


def diagnose(observations):

    for observation in observations:

        if (
            observation["loss"] >= 20
            and observation["delay"] >= 100
        ):
            return "RATE_LIMITED"

    return "NORMAL"


def print_results(
    strategy,
    environment,
    observations
):

    diagnosis = diagnose(
        observations
    )

    print()
    print("----------------------------------------")
    print(f"{strategy}")
    print("----------------------------------------")

    print(
        f"Ground truth : {environment}"
    )

    print(
        f"Diagnosis    : {diagnosis}"
    )

    print(
        f"Probes used  : {len(observations)}"
    )

    for observation in observations:

        print(
            f"{observation['rate']:4} pps | "
            f"Loss {observation['loss']:6.2f}% | "
            f"Delay {observation['delay']:7.2f} ms"
        )


def main():

    print()
    print("========================================")
    print(" PATHPROBE-AI")
    print(" ADAPTIVE VS FIXED EVALUATION")
    print("========================================")

    for environment in ["E0", "E1"]:

        print()
        print(
            f"========== {environment} =========="
        )

        fixed = fixed_strategy(
            environment
        )

        adaptive = adaptive_strategy(
            environment
        )

        print_results(
            "FIXED STRATEGY",
            environment,
            fixed
        )

        print_results(
            "ADAPTIVE STRATEGY",
            environment,
            adaptive
        )

        fixed_count = len(fixed)
        adaptive_count = len(adaptive)

        reduction = (
            (fixed_count - adaptive_count)
            / fixed_count
            * 100
        )

        print()
        print(
            f"Probe reduction: "
            f"{reduction:.2f}%"
        )


if __name__ == "__main__":
    main()
