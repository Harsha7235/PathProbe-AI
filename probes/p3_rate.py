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
OUTPUT_FILE = OUTPUT_DIR / "probe_observations.csv"


# ============================================================
# PROBE CONFIGURATION
# ============================================================

PROBE_ID = "P3"
PROBE_NAME = "rate_sweep"

RATES = [
    10,
    25,
    50,
    100,
    200,
    500
]


# ============================================================
# RUN ONE RATE EXPERIMENT
# ============================================================

def run_probe(rate):

    if not EXECUTABLE.exists():
        raise FileNotFoundError(
            f"P3 executable not found:\n{EXECUTABLE}\n\n"
            "Run './ns3 build' first."
        )

    command = [
        str(EXECUTABLE),
        f"--packetsPerSecond={rate}"
    ]

    print()
    print("----------------------------------------")
    print(f"P3 offered rate: {rate} packets/sec")
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
            f"P3 failed at {rate} packets/sec"
        )

    return result.stdout


# ============================================================
# EXTRACT VALUE
# ============================================================

def extract_value(pattern, output):

    match = re.search(pattern, output)

    if not match:
        raise ValueError(
            f"Could not extract value: {pattern}"
        )

    return float(match.group(1))


# ============================================================
# PARSE RESULT
# ============================================================

def parse_result(output, rate):

    packets_sent = int(
        extract_value(
            r"Packets Sent\s*:\s*(\d+)",
            output
        )
    )

    packets_received = int(
        extract_value(
            r"Packets Received\s*:\s*(\d+)",
            output
        )
    )

    packet_loss = extract_value(
        r"Packet Loss\s*:\s*([\d.]+)",
        output
    )

    throughput = extract_value(
        r"Throughput\s*:\s*([\d.]+)",
        output
    )

    delay = extract_value(
        r"Average Delay\s*:\s*([\d.]+)",
        output
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "probe_id": PROBE_ID,
        "probe_name": PROBE_NAME,
        "parameter": "packet_rate_pps",
        "parameter_value": rate,
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
        "probe_id",
        "probe_name",
        "parameter",
        "parameter_value",
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

    print()
    print("========================================")
    print("       PATHPROBE-AI P3 SWEEP")
    print("       RATE INVESTIGATION")
    print("========================================")

    results = []

    for rate in RATES:

        output = run_probe(rate)

        row = parse_result(
            output,
            rate
        )

        results.append(row)

    save_results(results)

    print()
    print("========================================")
    print("       P3 SWEEP COMPLETE")
    print("========================================")
    print()

    for row in results:

        print(
            f"{row['parameter_value']:4} pps | "
            f"Loss: {row['packet_loss_percent']:6.2f}% | "
            f"Throughput: {row['throughput_mbps']:8.6f} Mbps | "
            f"Delay: {row['average_delay_ms']:6.2f} ms"
        )

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
