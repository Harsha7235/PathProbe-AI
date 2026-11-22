import os
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_VERSION = "0.2.0"
MODEL = os.getenv("PATHPROBE_MODEL", "qwen3:8b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = LOG_DIR / "measurements.jsonl"

app = FastAPI(
    title="PATHPROBE AI",
    version=APP_VERSION,
    description="Topology-aware network diagnosis backend"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    topology: dict[str, Any] = Field(default_factory=dict)
    observations: Any = Field(default_factory=dict)
    question: str = "Analyze the reported network topology and observations."

class MeasurementReport(BaseModel):
    topology: dict[str, Any] = Field(default_factory=dict)
    observations: Any = Field(default_factory=dict)
    source: str = "Packet Tracer integration"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def build_report(topology, observations, source="Packet Tracer integration"):
    report = {
        "timestamp": utc_now(),
        "source": source,
        "topology": topology,
        "observations": observations,
        "measurements": {
            "rtt_ms": {"status": "NOT_MEASURED", "value": None},
            "jitter_ms": {"status": "NOT_MEASURED", "value": None},
            "packet_loss_percent": {"status": "NOT_MEASURED", "value": None},
            "throughput_mbps": {"status": "NOT_MEASURED", "value": None},
            "hop_count": {"status": "NOT_MEASURED", "value": None},
            "interface_errors": {"status": "NOT_COLLECTED", "value": None}
        },
        "note": "No active network probes or device CLI collection were performed."
    }
    canonical = json.dumps(report, sort_keys=True, default=str)
    report["report_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report

def save_report(report):
    with REPORT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, default=str) + "\n")

def read_reports():
    if not REPORT_FILE.exists():
        return []
    reports = []
    with REPORT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                reports.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return reports

def topology_summary(topology):
    devices = topology.get("devices", [])
    links = topology.get("links", [])
    return {
        "device_count": len(devices) if isinstance(devices, list) else None,
        "link_count": len(links) if isinstance(links, list) else None,
        "devices": devices if isinstance(devices, list) else [],
        "links": links if isinstance(links, list) else []
    }

def reported_down_links(topology, observations):
    found = []
    for link in topology.get("links", []) if isinstance(topology.get("links"), list) else []:
        if isinstance(link, dict):
            status = str(link.get("status", "")).lower()
            if status in ("down", "disconnected", "failed"):
                found.append(link)
    if isinstance(observations, dict):
        for link in observations.get("down_links", []):
            found.append(link)
    return found

def collection_errors(observations):
    if isinstance(observations, dict):
        return observations.get("collection_errors", [])
    return []

@app.get("/")
def root():
    return {
        "application": "PATHPROBE AI",
        "version": APP_VERSION,
        "status": "running",
        "model": MODEL,
        "endpoints": [
            "/", "/health", "/api/status", "/api/analyze",
            "/api/tools", "/api/tools/{tool_name}",
            "/api/measurements/report", "/api/measurements/latest"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION}

@app.get("/api/status")
def status():
    ollama = "unknown"
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        ollama = "connected" if r.ok else "error"
    except requests.RequestException:
        ollama = "unavailable"
    return {
        "application": "PATHPROBE AI",
        "version": APP_VERSION,
        "model": MODEL,
        "ollama": ollama,
        "measurement_log_exists": REPORT_FILE.exists()
    }

@app.get("/api/tools")
def list_tools():
    return {
        "version": APP_VERSION,
        "tools": [
            {
                "name": "summarize_topology",
                "description": "Summarize the topology data supplied to PATHPROBE AI.",
                "read_only": True
            },
            {
                "name": "list_reported_down_links",
                "description": "List links explicitly reported as down in supplied data.",
                "read_only": True
            },
            {
                "name": "list_collection_errors",
                "description": "List collection errors explicitly supplied to PATHPROBE AI.",
                "read_only": True
            }
        ]
    }

@app.post("/api/tools/{tool_name}")
def run_tool(tool_name: str, payload: dict[str, Any] = None):
    payload = payload or {}
    topology = payload.get("topology", {})
    observations = payload.get("observations", {})
    if tool_name == "summarize_topology":
        return topology_summary(topology)
    if tool_name == "list_reported_down_links":
        return {"down_links": reported_down_links(topology, observations)}
    if tool_name == "list_collection_errors":
        return {"collection_errors": collection_errors(observations)}
    raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

@app.post("/api/measurements/report")
def create_measurement_report(request: MeasurementReport):
    report = build_report(request.topology, request.observations, request.source)
    save_report(report)
    return report

@app.get("/api/measurements/latest")
def latest_measurement():
    reports = read_reports()
    if not reports:
        return {
            "status": "NO_REPORTS",
            "message": "No measurement reports exist yet. Submit a report or call /api/analyze."
        }
    return reports[-1]

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    report = build_report(request.topology, request.observations)
    save_report(report)

    prompt = f"""
You are PATHPROBE AI, a careful network diagnosis assistant.
Analyze only the supplied topology and observations.
Do not claim to have run ping, traceroute, packet capture, device CLI,
or any other probe unless the input explicitly contains its results.
Separate observed facts, inferences, and unknowns.
Do not invent IP addresses, links, device states, measurements, or causes.
Recommend safe next diagnostic steps. Do not apply configuration changes.

User question:
{request.question}

Supplied topology:
{json.dumps(request.topology, indent=2, default=str)}

Supplied observations:
{json.dumps(request.observations, indent=2, default=str)}

Measurement report:
{json.dumps(report, indent=2, default=str)}
"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("message", {}).get("content", "")
        if not answer:
            answer = "The model returned an empty response."
        return {
            "application": "PATHPROBE AI",
            "version": APP_VERSION,
            "answer": answer,
            "measurement_report": report
        }
    except requests.RequestException as exc:
        return {
            "application": "PATHPROBE AI",
            "version": APP_VERSION,
            "answer": "The measurement report was saved, but Ollama could not be reached. Check that Ollama is running and the model is available.",
            "error": str(exc),
            "measurement_report": report
        }

