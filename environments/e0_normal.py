import csv
import re
import subprocess
from pathlib import Path
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")
NS3_DIR = Path("/home/harsha/ns-3.48")

EXECUTABLE = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_rate-default"
)

OUTPUT_DIR = PROJECT_DIR / "dataset" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "environment_observations.csv"


# ============================================================
# ENVIRONMENT
# ============================================================

ENVIRONMENT_ID = "E0"
ENVIRONMENT_NAME = "normal"

RATES = [
    10,
    25,
    50,
    100,
    200,
    500
]


# ============================================================
# RUN EXPERIMENT
# ============================================================

def run_experiment(rate):

    command = [
        str(EXECUTABLE),
        f"--packetsPerSecond={rate}"
    ]

    print()
    print("----------------------------------------")
    print(f"E0 | {rate} packets/sec")
    print("----------------------------------------")

    result = subprocess.run(
        command,
        cwd=NS3_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            f"E0 experiment failed at {rate} pps"
        )

    return result.stdout


# ============================================================
# EXTRACT VALUE
# ============================================================

def extract(pattern, output):

    match = re.search(pattern, output)

    if not match:
        raise ValueError(
            f"Could not extract: {pattern}"
        )

    return float(match.group(1))


# ============================================================
# PARSE RESULT
# ============================================================

def parse_result(output, rate):

    packets_sent = int(
        extract(
            r"Packets Sent\s*:\s*(\d+)",
            output
        )
    )

    packets_received = int(
        extract(
            r"Packets Received\s*:\s*(\d+)",
            output
        )
    )

    packet_loss = extract(
        r"Packet Loss\s*:\s*([\d.]+)",
        output
    )

    throughput = extract(
        r"Throughput\s*:\s*([\d.]+)",
        output
    )

    delay = extract(
        r"Average Delay\s*:\s*([\d.]+)",
        output
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "environment_id": ENVIRONMENT_ID,
        "environment_name": ENVIRONMENT_NAME,
        "rate_limit": "none",
        "probe_parameter": "packet_rate_pps",
        "probe_value": rate,
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss_percent": packet_loss,
        "throughput_mbps": throughput,
        "average_delay_ms": delay
    }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "timestamp",
        "environment_id",
        "environment_name",
        "rate_limit",
        "probe_parameter",
        "probe_value",
        "packets_sent",
        "packets_received",
        "packet_loss_percent",
        "throughput_mbps",
        "average_delay_ms"
    ]

    file_exists = OUTPUT_FILE.exists()

    with open(
        OUTPUT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(results)


# ============================================================
# MAIN
# ============================================================

def main():

    if not EXECUTABLE.exists():
        raise FileNotFoundError(
            f"E0 executable not found:\n{EXECUTABLE}\n\n"
            "Run ./ns3 build in ~/ns-3.48 first."
        )

    print()
    print("========================================")
    print("     PATHPROBE-AI E0 EXPERIMENT")
    print("     NORMAL ENVIRONMENT")
    print("========================================")
    print()
    print(f"Environment : {ENVIRONMENT_ID}")
    print(f"Condition   : {ENVIRONMENT_NAME}")
    print("Rate Limit  : none")

    results = []

    for rate in RATES:

        output = run_experiment(rate)

        row = parse_result(
            output,
            rate
        )

        results.append(row)

    save_results(results)

    print()
    print("========================================")
    print("       E0 EXPERIMENT COMPLETE")
    print("========================================")
    print()

    for row in results:

        print(
            f"{row['probe_value']:4} pps | "
            f"Loss: {row['packet_loss_percent']:6.2f}% | "
            f"Throughput: {row['throughput_mbps']:8.6f} Mbps | "
            f"Delay: {row['average_delay_ms']:7.2f} ms"
        )

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
