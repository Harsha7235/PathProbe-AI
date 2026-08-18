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
    / "ns3.48-pathprobe_packet_size-default"
)

OUTPUT_DIR = PROJECT_DIR / "dataset" / "raw"

OUTPUT_FILE = OUTPUT_DIR / "probe_observations.csv"


# ============================================================
# PROBE CONFIGURATION
# ============================================================

PROBE_ID = "P2"

PROBE_NAME = "packet_size_sweep"

PACKET_SIZES = [
    64,
    128,
    256,
    512,
    1024,
    1200,
    1400,
    1500,
    1600
]


# ============================================================
# RUN ONE PACKET-SIZE EXPERIMENT
# ============================================================

def run_probe(packet_size):

    command = [
        str(EXECUTABLE),
        f"--packetSize={packet_size}"
    ]

    print()
    print("----------------------------------------")
    print(f"P2 packet size: {packet_size} bytes")
    print("----------------------------------------")

    result = subprocess.run(
        command,
        cwd=NS3_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:

        print(result.stdout)
        print(result.stderr)

        raise RuntimeError(
            f"P2 failed for packet size {packet_size}"
        )

    print(result.stdout)

    return result.stdout


# ============================================================
# EXTRACT VALUE
# ============================================================

def extract_value(pattern, output):

    match = re.search(
        pattern,
        output
    )

    if not match:

        raise ValueError(
            f"Could not find value: {pattern}"
        )

    return float(match.group(1))


# ============================================================
# PARSE RESULT
# ============================================================

def parse_result(output, packet_size):

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
        "packet_size_bytes": packet_size,
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
        "packet_size_bytes",
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

        for row in results:
            writer.writerow(row)


# ============================================================
# MAIN
# ============================================================

def main():

    if not EXECUTABLE.exists():

        raise FileNotFoundError(
            f"P2 executable not found:\n{EXECUTABLE}\n\n"
            "Run './ns3 build' in ~/ns-3.48 first."
        )

    print()
    print("========================================")
    print("      PATHPROBE-AI P2 SWEEP")
    print("      PACKET-SIZE INVESTIGATION")
    print("========================================")

    results = []

    for packet_size in PACKET_SIZES:

        output = run_probe(
            packet_size
        )

        row = parse_result(
            output,
            packet_size
        )

        results.append(row)

    save_results(
        results
    )

    print()
    print("========================================")
    print("       P2 SWEEP COMPLETE")
    print("========================================")
    print()

    for row in results:

        print(
            f"{row['packet_size_bytes']:5} B | "
            f"Loss: {row['packet_loss_percent']:6.2f}% | "
            f"Throughput: {row['throughput_mbps']:8.6f} Mbps | "
            f"Delay: {row['average_delay_ms']:6.2f} ms"
        )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()