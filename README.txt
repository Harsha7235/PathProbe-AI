PATHPROBE AI — Measurement Engine Starter v0.2
==============================================

Files:
- pathprobe_backend.py: complete FastAPI backend replacement, including existing
  health/status/analyze endpoints and new measurement/tool endpoints.
- measurement_engine.py: provenance-labelled report from the real Packet Tracer
  topology snapshot.
- agent_tools.py: read-only allow-listed tools.
- pathprobe_backend_additions.txt: optional API reference.

INSTALL SAFELY
--------------
1. Stop the currently running PATHPROBE backend with Ctrl+C in its PowerShell
   window.
2. Back up C:\PATHPROBE_AI\pathprobe_backend.py, for example:
      Copy-Item C:\PATHPROBE_AI\pathprobe_backend.py C:\PATHPROBE_AI\pathprobe_backend_backup.py
3. Copy the three .py files from this package into C:\PATHPROBE_AI\, replacing
   pathprobe_backend.py only after the backup is made.
4. Start it:
      Set-Location C:\PATHPROBE_AI
      .\.venv\Scripts\python.exe -m uvicorn pathprobe_backend:app --host 127.0.0.1 --port 8000
5. Test:
      Invoke-RestMethod http://127.0.0.1:8000/api/tools | ConvertTo-Json -Depth 6
      Invoke-RestMethod http://127.0.0.1:8000/api/status | ConvertTo-Json -Depth 5

New endpoint:
- POST /api/measurements/report
- GET /api/measurements/latest
- GET /api/tools
- POST /api/tools/summarize_topology
- POST /api/tools/list_reported_down_links
- POST /api/tools/list_collection_errors

The existing HTML already sends the current snapshot to /api/analyze. That
endpoint now automatically creates and stores a measurement report on every
successful analysis request. Reports are appended to:
    C:\PATHPROBE_AI\logs\measurements.jsonl

IMPORTANT LIMITATIONS
---------------------
This version only records information already collected by Packet Tracer's
Script Module. RTT, jitter, packet loss, throughput, HTTP, DNS, routing tables,
and VLAN configuration are explicitly marked as not measured/not collected.
No active probes, arbitrary shell commands, device CLI execution, or
configuration changes are enabled.
