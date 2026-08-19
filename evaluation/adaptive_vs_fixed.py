import csv
import subprocess
from pathlib import Path
from statistics import mean

NS3_DIR = Path("/home/harsha/ns-3.48")

ENVIRONMENTS = {
    "E0": {
        "name": "NORMAL",
        "binary": "build/scratch/ns3.48-pathprobe_rate-default",
    },
    "E1": {
        "name": "RATE_LIMITED",
        "binary": "build/scratch/ns3.48-pathprobe_rate_limited-default",
    },
    "E2": {
        "name": "DELAY",
        "binary": "build/scratch/ns3.48-pathprobe_delay_jitter-default",
    },
}

PROBE_RATES = [50, 100, 200, 500]


def run_probe(environment, rate):
    binary = NS3_DIR / ENVIRONMENTS[environment]["binary"]

    command = [
        str(binary),
        f"--packetsPerSecond={rate}",
    ]

    if environment == "E1":
        command.append("--rateLimit=1Mbps")

    result = subprocess.run(
        command,
        cwd=NS3_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ns-3 failed for {environment} at {rate} pps\n"
            + result.stderr
        )

    output = result.stdout

    metrics = {
        "rate": rate,
        "loss": 0.0,
        "delay": 0.0,
        "throughput": 0.0,
    }

    for line in output.splitlines():
        line = line.strip()

        if line.startswith("Packet Loss"):
            metrics["loss"] = float(
                line.split(":")[1].replace("%", "").strip()
            )

        elif line.startswith("Average Delay"):
            metrics["delay"] = float(
                line.split(":")[1].replace("ms", "").strip()
            )

        elif line.startswith("Throughput"):
            metrics["throughput"] = float(
                line.split(":")[1].replace("Mbps", "").strip()
            )

    return metrics


def classify(observations):
    if not observations:
        return "UNKNOWN"

    latest = observations[-1]

    # Strong rate-limited signature
    for obs in observations:
        if obs["loss"] > 5 and obs["delay"] >= 100:
            return "RATE_LIMITED"

    # Persistent delay signature
    high_delay = [
        obs for obs in observations
        if obs["delay"] >= 100 and obs["loss"] == 0
    ]

    if len(high_delay) >= 2:
        return "DELAY"

    # Normal only after high-load validation
    if (
        latest["rate"] >= 200
        and latest["loss"] == 0
        and latest["delay"] < 50
    ):
        return "NORMAL"

    return "UNKNOWN"


def adaptive_strategy(environment):
    observations = []

    for rate in PROBE_RATES:
        result = run_probe(environment, rate)
        observations.append(result)

        diagnosis = classify(observations)

        if diagnosis != "UNKNOWN":
            return diagnosis, observations

    return classify(observations), observations


def fixed_strategy(environment):
    observations = []

    for rate in PROBE_RATES:
        result = run_probe(environment, rate)
        observations.append(result)

    return classify(observations), observations


def print_result(
    environment,
    strategy,
    diagnosis,
    observations,
):
    print()
    print("----------------------------------------")
    print(f"Environment : {environment}")
    print(f"Strategy    : {strategy}")
    print(f"Diagnosis   : {diagnosis}")
    print(f"Probes      : {len(observations)}")
    print("----------------------------------------")

    for obs in observations:
        print(
            f"{obs['rate']:>4} pps | "
            f"Loss {obs['loss']:>6.2f}% | "
            f"Delay {obs['delay']:>7.2f} ms | "
            f"TP {obs['throughput']:>8.4f} Mbps"
        )


def main():
    print()
    print("========================================")
    print("   PATHPROBE-AI")
    print("   ADAPTIVE VS FIXED EVALUATION")
    print("========================================")

    results = []

    for environment in ENVIRONMENTS:
        print()
        print(f"========== TESTING {environment} ==========")

        adaptive_diag, adaptive_obs = adaptive_strategy(
            environment
        )

        fixed_diag, fixed_obs = fixed_strategy(
            environment
        )

        actual = ENVIRONMENTS[environment]["name"]

        print_result(
            environment,
            "ADAPTIVE",
            adaptive_diag,
            adaptive_obs,
        )

        print_result(
            environment,
            "FIXED",
            fixed_diag,
            fixed_obs,
        )

        results.append({
            "environment": environment,
            "actual": actual,
            "adaptive_diagnosis": adaptive_diag,
            "adaptive_probes": len(adaptive_obs),
            "fixed_diagnosis": fixed_diag,
            "fixed_probes": len(fixed_obs),
        })

    adaptive_accuracy = mean(
        r["adaptive_diagnosis"] == r["actual"]
        for r in results
    )

    fixed_accuracy = mean(
        r["fixed_diagnosis"] == r["actual"]
        for r in results
    )

    adaptive_avg = mean(
        r["adaptive_probes"]
        for r in results
    )

    fixed_avg = mean(
        r["fixed_probes"]
        for r in results
    )

    reduction = (
        (fixed_avg - adaptive_avg)
        / fixed_avg
        * 100
    )

    print()
    print("========================================")
    print("          FINAL COMPARISON")
    print("========================================")

    print(
        f"Adaptive Accuracy       : "
        f"{adaptive_accuracy * 100:.2f}%"
    )

    print(
        f"Fixed Accuracy          : "
        f"{fixed_accuracy * 100:.2f}%"
    )

    print(
        f"Adaptive Avg Probes     : "
        f"{adaptive_avg:.2f}"
    )

    print(
        f"Fixed Avg Probes        : "
        f"{fixed_avg:.2f}"
    )

    print(
        f"Probe Reduction         : "
        f"{reduction:.2f}%"
    )

    print()
    print("Environment Results")
    print("----------------------------------------")

    for r in results:
        print(
            f"{r['environment']} | "
            f"Actual: {r['actual']} | "
            f"Adaptive: {r['adaptive_diagnosis']} "
            f"({r['adaptive_probes']} probes) | "
            f"Fixed: {r['fixed_diagnosis']} "
            f"({r['fixed_probes']} probes)"
        )

    output_dir = Path(
        "/mnt/c/Projects/PathProbe-AI/dataset/results"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir / "adaptive_vs_fixed.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print(
        f"Saved results to: {output_file}"
    )


if __name__ == "__main__":
    main()
