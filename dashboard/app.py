from flask import Flask, render_template, jsonify
from pathlib import Path
import csv
import json
from datetime import datetime

app = Flask(__name__)

# ============================================================
# PATHPROBE-AI DASHBOARD
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "dataset"

ENVIRONMENT_FILE = DATA_DIR / "raw" / "environment_observations.csv"
ADAPTIVE_FILE = DATA_DIR / "results" / "adaptive_vs_fixed.csv"
INVESTIGATION_FILE = DATA_DIR / "results" / "investigation_results.csv"
ROBUSTNESS_FILE = DATA_DIR / "results" / "robustness_results.csv"
FINAL_FILE = DATA_DIR / "results" / "final_evaluation.json"


# ============================================================
# HELPERS
# ============================================================

def read_csv_file(path):

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_json_file(path):

    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def to_float(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


# ============================================================
# DATA PROCESSING
# ============================================================

def get_environment_data():

    rows = read_csv_file(ENVIRONMENT_FILE)

    result = {
        "E0": [],
        "E1": [],
        "E2": []
    }

    for row in rows:

        environment = row.get("environment_id")

        if environment not in result:
            continue

        result[environment].append({
            "rate": to_int(row.get("probe_value")),
            "loss": to_float(row.get("packet_loss_percent")),
            "delay": to_float(row.get("average_delay_ms")),
            "throughput": to_float(row.get("throughput_mbps")),
            "sent": to_int(row.get("packets_sent")),
            "received": to_int(row.get("packets_received"))
        })

    for environment in result:
        result[environment].sort(
            key=lambda x: x["rate"]
        )

    return result


def get_adaptive_results():

    rows = read_csv_file(ADAPTIVE_FILE)

    result = []

    for row in rows:

        result.append({
            "environment": row.get("environment"),
            "actual": row.get("actual"),
            "adaptive": row.get("adaptive_diagnosis"),
            "adaptive_probes": to_int(
                row.get("adaptive_probes")
            ),
            "fixed": row.get("fixed_diagnosis"),
            "fixed_probes": to_int(
                row.get("fixed_probes")
            )
        })

    return result


def get_latest_investigation():

    rows = read_csv_file(INVESTIGATION_FILE)

    if not rows:
        return {}

    latest = rows[-1]

    return {
        "timestamp": latest.get("timestamp"),
        "environment": latest.get("environment"),
        "diagnosis": latest.get("diagnosis"),
        "confidence": to_float(
            latest.get("confidence")
        ),
        "probes": to_int(
            latest.get("probes_used")
        ),
        "probe_reduction": to_float(
            latest.get("probe_reduction_percent")
        )
    }


def get_robustness():

    rows = read_csv_file(ROBUSTNESS_FILE)

    if not rows:
        return {
            "accuracy": 0,
            "passed": 0,
            "total": 0,
            "confidence": 0,
            "probes": 0
        }

    passed = 0
    confidence_total = 0
    probes_total = 0

    for row in rows:

        if (
            row.get("diagnosis")
            == row.get("actual")
        ):
            passed += 1

        confidence_total += to_float(
            row.get("confidence")
        )

        probes_total += to_int(
            row.get("probes")
        )

    total = len(rows)

    return {
        "accuracy": (
            passed / total * 100
            if total else 0
        ),
        "passed": passed,
        "total": total,
        "confidence": (
            confidence_total / total
            if total else 0
        ),
        "probes": (
            probes_total / total
            if total else 0
        )
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


@app.route("/api/dashboard")
def dashboard_data():

    environment_data = get_environment_data()

    adaptive = get_adaptive_results()

    investigation = get_latest_investigation()

    robustness = get_robustness()

    final = read_json_file(
        FINAL_FILE
    )

    return jsonify({

        "project": {
            "name": "PATHPROBE-AI",
            "description":
                "Autonomous Network Diagnosis "
                "and Adaptive Probing",
            "status": "OPERATIONAL"
        },

        "investigation": investigation,

        "environments": environment_data,

        "adaptive_results": adaptive,

        "robustness": robustness,

        "final_evaluation": final
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "project": "PathProbe-AI"
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("              PATHPROBE-AI DASHBOARD")
    print("=" * 60)
    print()
    print("Dashboard:")
    print("http://127.0.0.1:5000")
    print()
    print("API:")
    print("http://127.0.0.1:5000/api/dashboard")
    print()
    print("Health:")
    print("http://127.0.0.1:5000/health")
    print()
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
