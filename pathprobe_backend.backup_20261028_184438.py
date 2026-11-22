from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from measurement_engine import build_measurement_report, append_jsonl
from agent_tools import tool_registry, run_tool


# ============================================================
# PATHPROBE AI CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:8b"

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
MEASUREMENT_LOG = LOG_DIR / "measurements.jsonl"

APP_NAME = "PATHPROBE AI"
APP_VERSION = "0.2.0"


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are PATHPROBE AI, an evidence-based network diagnosis agent
integrated with Cisco Packet Tracer.

Analyze only the supplied topology and observations.

Separate:
1. Observed facts
2. Derived facts
3. Hypotheses
4. Recommendations

Never invent measurements, devices, configurations, or test results.

Never claim that you executed a probe or repaired a device unless
a real tool result confirms it.

A link being UP does not prove end-to-end connectivity or service
availability.

If evidence is insufficient, explain what is missing and recommend
the next appropriate test.

No active network probes or device configuration changes are
available in this backend version.

Do not fabricate RTT, jitter, packet loss, throughput, or other
network measurements.
"""


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 56)
    print(f"{APP_NAME} backend starting - version {APP_VERSION}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"AI model: {OLLAMA_MODEL}")
    print(f"Measurement log: {MEASUREMENT_LOG}")
    print("=" * 56)

    yield

    print("PATHPROBE AI backend stopped.")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=(
        "Local network diagnosis backend with "
        "evidence-labelled measurements."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
) 


# ============================================================
# CORS CONFIGURATION
# Allows the Packet Tracer interface to call the local backend.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST AND RESPONSE MODELS
# ============================================================

class DiagnosisRequest(BaseModel):
    question: str = Field(
        default="Analyze the network and identify possible faults.",
        min_length=1,
        max_length=4000,
    )

    topology: dict[str, Any] = Field(
        default_factory=dict
    )

    observations: list[dict[str, Any]] = Field(
        default_factory=list
    )


class DiagnosisResponse(BaseModel):
    status: str
    model: str
    timestamp: str
    diagnosis: str


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "model": OLLAMA_MODEL,
        "endpoints": [
            "/",
            "/health",
            "/api/status",
            "/api/analyze",
            "/api/tools",
            "/api/measurements/report",
            "/api/measurements/latest",
        ],
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# BACKEND AND OLLAMA STATUS
# ============================================================

@app.get("/api/status")
async def api_status():
    ollama_status = "unknown"
    installed_models: list[str] = []
    error = None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{OLLAMA_URL}/api/tags"
            )

            response.raise_for_status()
            data = response.json()

            installed_models = [
                item.get("name", "")
                for item in data.get("models", [])
            ]

            ollama_status = (
                "connected"
                if any(
                    name == OLLAMA_MODEL
                    or name.startswith(OLLAMA_MODEL + ":")
                    for name in installed_models
                )
                else "model_not_found"
            )

    except Exception as exc:
        ollama_status = "unavailable"
        error = str(exc)

    return {
        "application": APP_NAME,
        "backend": "running",
        "version": APP_VERSION,
        "ollama": ollama_status,
        "configured_model": OLLAMA_MODEL,
        "installed_models": installed_models,
        "error": error,
    }


# ============================================================
# AVAILABLE READ-ONLY DIAGNOSTIC TOOLS
# ============================================================

@app.get("/api/tools")
async def get_tools():
    return {
        "status": "success",
        "execution_policy": "read_only_allow_list",
        "tools": tool_registry(),
        "not_enabled": [
            "ping_or_icmp_probe",
            "http_service_probe",
            "dns_query",
            "throughput_measurement",
            "jitter_measurement",
            "device_cli_execution",
            "configuration_changes",
        ],
    }


# ============================================================
# CREATE A MEASUREMENT REPORT
# ============================================================

@app.post("/api/measurements/report")
async def measurements_report(request: DiagnosisRequest):
    report = build_measurement_report(
        request.topology,
        request.observations,
    )

    append_jsonl(
        report,
        MEASUREMENT_LOG,
    )

    return report


# ============================================================
# GET THE LATEST MEASUREMENT REPORT
# ============================================================

@app.get("/api/measurements/latest")
async def measurements_latest():
    if not MEASUREMENT_LOG.exists():
        raise HTTPException(
            status_code=404,
            detail="No measurement report has been recorded yet.",
        )

    try:
        import json

        last_line = ""

        with MEASUREMENT_LOG.open(
            "r",
            encoding="utf-8",
        ) as stream:
            for line in stream:
                if line.strip():
                    last_line = line

        if not last_line:
            raise ValueError(
                "Measurement log is empty."
            )

        return json.loads(last_line)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Could not read latest measurement report: "
                f"{exc}"
            ),
        )


# ============================================================
# EXECUTE A READ-ONLY DIAGNOSTIC TOOL
# ============================================================

@app.post("/api/tools/{tool_name}")
async def execute_read_only_tool(
    tool_name: str,
    request: DiagnosisRequest,
):
    result = run_tool(
        tool_name,
        request.topology,
        request.observations,
    )

    if result.get("status") == "rejected":
        raise HTTPException(
            status_code=400,
            detail=result.get("error"),
        )

    return result


# ============================================================
# MAIN AI NETWORK DIAGNOSIS ENDPOINT
# ============================================================

@app.post(
    "/api/analyze",
    response_model=DiagnosisResponse,
)
async def analyze_network(request: DiagnosisRequest):

    # Require actual topology or observations.
    if not request.topology and not request.observations:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide topology information or observations "
                "before diagnosis."
            ),
        )

    # --------------------------------------------------------
    # Generate and save a measurement report.
    # Unavailable measurements remain unavailable.
    # --------------------------------------------------------

    report = build_measurement_report(
        request.topology,
        request.observations,
    )

    append_jsonl(
        report,
        MEASUREMENT_LOG,
    )

    # --------------------------------------------------------
    # Construct the AI prompt.
    # --------------------------------------------------------

    user_message = f"""
NETWORK QUESTION:
{request.question}

NETWORK TOPOLOGY DATA:
{request.topology}

OBSERVED NETWORK DATA:
{request.observations}

MEASUREMENT REPORT:
{report}

Analyze only the information supplied above.

Clearly distinguish observed facts from derived counts,
hypotheses, and recommendations.

Do not claim that you performed any network test or changed
a device configuration.

If a metric is marked NOT_MEASURED or NOT_COLLECTED,
treat it as unavailable.
"""

    # --------------------------------------------------------
    # Ollama request
    # --------------------------------------------------------

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
    }

    try:
        async with httpx.AsyncClient(
            timeout=180.0
        ) as client:

            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=(
                "Ollama timed out. Check model loading "
                "and system resources."
            ),
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Ollama returned HTTP "
                f"{exc.response.status_code}."
            ),
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Ollama. Confirm "
                "Ollama is running on localhost:11434. "
                f"Details: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Extract AI diagnosis
    # --------------------------------------------------------

    diagnosis = str(
        data.get("message", {}).get("content", "")
    ).strip()

    if not diagnosis:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an empty diagnosis.",
        )

    # --------------------------------------------------------
    # Return diagnosis to the frontend
    # --------------------------------------------------------

    return DiagnosisResponse(
        status="success",
        model=OLLAMA_MODEL,
        timestamp=datetime.now(
            timezone.utc
        ).isoformat(),
        diagnosis=diagnosis,
    )


# ============================================================
# OPTIONAL DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "pathprobe_backend:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )