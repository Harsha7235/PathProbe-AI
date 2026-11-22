from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# PATHPROBE AI CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:8b"

APP_NAME = "PATHPROBE AI"
APP_VERSION = "0.1.0"

SYSTEM_PROMPT = """
You are PATHPROBE AI, an evidence-based network diagnosis agent
integrated with Cisco Packet Tracer.

Your responsibilities:
1. Analyze the supplied network topology and observations.
2. Identify possible network faults.
3. Distinguish observed facts from hypotheses.
4. Recommend specific tests to distinguish competing hypotheses.
5. Explain your reasoning clearly.
6. Never invent measurements, device configurations, or test results.
7. Never claim a fault is confirmed without sufficient evidence.
8. Never claim you executed a command or repaired a device unless
   a real tool execution result explicitly confirms it.
9. Do not invent devices or connections absent from the supplied data.
10. If evidence is insufficient, explain exactly what is missing.

Use these sections in your response:

OBSERVED EVIDENCE
POSSIBLE ROOT CAUSES
RECOMMENDED NEXT TESTS
CONFIDENCE AND LIMITATIONS

Clearly label facts, hypotheses, and recommendations.
"""


# ============================================================
# APPLICATION
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print(f"{APP_NAME} backend starting")
    print(f"Version: {APP_VERSION}")
    print(f"Ollama model: {OLLAMA_MODEL}")
    print(f"Ollama endpoint: {OLLAMA_URL}")
    print("=" * 60)
    yield
    print("PATHPROBE AI backend stopped.")


app = FastAPI(
    title=APP_NAME,
    description=(
        "Local, evidence-based network diagnosis backend "
        "for Cisco Packet Tracer."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

# The backend binds to localhost only when launched with the
# uvicorn command supplied later.
#
# CORS is enabled for the initial local integration test.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class DiagnosisRequest(BaseModel):
    question: str = Field(
        default="Analyze the network and identify possible faults.",
        min_length=1,
        max_length=4000,
    )

    topology: dict[str, Any] = Field(default_factory=dict)

    observations: list[dict[str, Any]] = Field(
        default_factory=list
    )


class DiagnosisResponse(BaseModel):
    status: str
    model: str
    timestamp: str
    diagnosis: str


# ============================================================
# HEALTH AND STATUS ENDPOINTS
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
        ],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
        "backend": "running",
        "ollama": ollama_status,
        "configured_model": OLLAMA_MODEL,
        "installed_models": installed_models,
        "error": error,
    }


# ============================================================
# AI DIAGNOSIS ENDPOINT
# ============================================================

@app.post("/api/analyze", response_model=DiagnosisResponse)
async def analyze_network(request: DiagnosisRequest):

    # Do not send an empty request to the model.
    if not request.topology and not request.observations:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide topology information or observations "
                "before requesting a diagnosis."
            ),
        )

    user_message = f"""
NETWORK QUESTION:
{request.question}

NETWORK TOPOLOGY DATA:
{request.topology}

OBSERVED NETWORK DATA:
{request.observations}

Analyze only the information supplied above.

Do not claim that you performed any network test.
Recommend the next test when the evidence is insufficient.
"""

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
        async with httpx.AsyncClient(timeout=180.0) as client:
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
                "Ollama timed out. Check model loading and "
                "available system resources."
            ),
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama returned HTTP "
                f"{exc.response.status_code}."
            ),
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Ollama. Confirm that "
                "Ollama is running on localhost:11434. "
                f"Details: {exc}"
            ),
        )

    diagnosis = (
        data.get("message", {}).get("content", "")
    ).strip()

    if not diagnosis:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an empty diagnosis.",
        )

    return DiagnosisResponse(
        status="success",
        model=OLLAMA_MODEL,
        timestamp=datetime.now(timezone.utc).isoformat(),
        diagnosis=diagnosis,
    )


# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "pathprobe_backend:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )