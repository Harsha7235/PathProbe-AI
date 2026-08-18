import csv
import re
import subprocess
from pathlib import Path
from datetime import datetime


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_DIR = Path("/mnt/c/Projects/PathProbe-AI")
NS3_DIR = Path("/home/harsha/ns-3.48")

OUTPUT_DIR = PROJECT_DIR / "dataset" / "raw"

OUTPUT_FILE = OUTPUT_DIR / "probe_observations.csv"


# ============================================================
# PROBE CONFIGURATION
# ============================================================

PROBE_ID = "P1"
PROBE_NAME = "baseline"


# IMPORTANT:
# Change this ONLY if your current working ns-3 command
# uses a different target.

NS3_TARGET = "scratch/pathprobe/pathprobe_baseline"


# ============================================================
# RUN NS-3
# ============================================================

def run_ns3():

    executable = (
        NS3_DIR
        / "build"
        / "scratch"
        / "pathprobe"
        / "ns3.48-pathprobe_baseline-default"
    )

    command = [
        str(executable)
    ]

    print()
    print("========================================")
    print("        PATHPROBE P1")
    print("        BASELINE PROBE")
    print("========================================")
    print()

    if not executable.exists():
        raise FileNotFoundError(
            f"ns-3 executable not found:\n{executable}\n\n"
            "Run './ns3 build' inside ns-3 first."
        )

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
            "P1 ns-3 execution failed."
        )

    return result.stdout

# ============================================================
# EXTRACT NS-3 RESULTS
# ============================================================

def extract_value(pattern, output):

    match = re.search(
        pattern,
        output
    )

    if not match:

        raise ValueError(
            f"Could not extract: {pattern}"
        )

    return float(match.group(1))


def parse_results(output):

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
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss_percent": packet_loss,
        "throughput_mbps": throughput,
        "average_delay_ms": delay
    }


# ============================================================
# SAVE STANDARDIZED OBSERVATION
# ============================================================

def save_observation(results):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "timestamp",
        "probe_id",
        "probe_name",
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

        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "probe_id": PROBE_ID,
            "probe_name": PROBE_NAME,
            **results
        })


# ============================================================
# MAIN
# ============================================================

def main():

    output = run_ns3()

    results = parse_results(
        output
    )

    save_observation(
        results
    )

    print()
    print("========================================")
    print("       P1 OBSERVATION SAVED")
    print("========================================")
    print()

    for key, value in results.items():

        print(
            f"{key:25} : {value}"
        )

    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()