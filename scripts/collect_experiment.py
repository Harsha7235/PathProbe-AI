import csv
import re
import subprocess
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")

CSV_FILE = (
    PROJECT_DIR
    / "dataset"
    / "raw"
    / "pathprobe_results.csv"
)

NS3_DIR = Path("/home/harsha/ns-3.48")


# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

EXPERIMENT_ID = "B0_001"
SCENARIO = "baseline"

PACKET_SIZE = 1024
MAX_PACKETS = 1000
PACKET_INTERVAL_MS = 10


# ============================================================
# RUN NS-3 EXPERIMENT
# ============================================================

def run_experiment():

    command = [
        "./ns3",
        "run",
        "scratch/pathprobe/pathprobe_baseline"
    ]

    print("========================================")
    print("      PATHPROBE-AI EXPERIMENT")
    print("========================================")
    print()
    print("Experiment ID :", EXPERIMENT_ID)
    print("Scenario      :", SCENARIO)
    print()
    print("Running ns-3...")
    print()

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

        print("========================================")
        print("ERROR: ns-3 experiment failed")
        print("========================================")
        print()

        print(result.stderr)

        raise RuntimeError(
            "ns-3 experiment failed"
        )

    return result.stdout


# ============================================================
# EXTRACT VALUE FROM NS-3 OUTPUT
# ============================================================

def extract_value(pattern, text):

    match = re.search(
        pattern,
        text
    )

    if not match:

        raise ValueError(
            f"Could not find value using pattern: {pattern}"
        )

    return float(match.group(1))


# ============================================================
# EXTRACT EXPERIMENT RESULTS
# ============================================================

def extract_results(output):

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

    average_delay = extract_value(
        r"Average Delay\s*:\s*([\d.]+)",
        output
    )

    return {
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss_percent": packet_loss,
        "throughput_mbps": throughput,
        "average_delay_ms": average_delay
    }


# ============================================================
# SAVE RESULT TO CSV
# ============================================================

def save_result(results):

    CSV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = CSV_FILE.exists()

    columns = [
        "experiment_id",
        "scenario",
        "packet_size_bytes",
        "max_packets",
        "packet_interval_ms",
        "packets_sent",
        "packets_received",
        "packet_loss_percent",
        "throughput_mbps",
        "average_delay_ms"
    ]

    with open(
        CSV_FILE,
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

        row = {
            "experiment_id": EXPERIMENT_ID,
            "scenario": SCENARIO,
            "packet_size_bytes": PACKET_SIZE,
            "max_packets": MAX_PACKETS,
            "packet_interval_ms": PACKET_INTERVAL_MS,
            **results
        }

        writer.writerow(row)

    print()
    print("========================================")
    print("       DATASET UPDATED")
    print("========================================")
    print()
    print("File:")
    print(CSV_FILE)
    print()
    print("Recorded results:")

    for key, value in results.items():

        print(
            f"{key:25} : {value}"
        )

    print()
    print("========================================")


# ============================================================
# MAIN
# ============================================================

def main():

    output = run_experiment()

    results = extract_results(
        output
    )

    save_result(
        results
    )


if __name__ == "__main__":

    main()
