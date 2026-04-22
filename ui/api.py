"""
ui/api.py
─────────
FastAPI backend — REST interface for the pipeline.
Useful for integrating into larger systems or CI/CD.

Run with: uvicorn ui.api:app --reload --port 8000

Endpoints:
  POST /run          — Start the full pipeline (async)
  GET  /status/{id}  — Check run status
  POST /approve/{id} — Submit human approvals
  GET  /results/{id} — Fetch final results
  GET  /health       — Health check
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Multi-Agent Outreach System API",
    description="REST API for the 5-agent research and outreach automation pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory run store (use Redis in production)
runs: Dict[str, Dict[str, Any]] = {}


# ── Request / Response models ─────────────────────────────────────────────────

class RunRequest(BaseModel):
    search_query: str = "topic:machine-learning stars:>200 pushed:>2024-01-01"
    max_projects: int = 5


class ApprovalRequest(BaseModel):
    approved_indices: List[int]          # Indices of approved emails
    edited_bodies: Optional[Dict[int, str]] = None   # {index: new_body}


class RunStatus(BaseModel):
    run_id: str
    status: str           # queued | running | awaiting_approval | complete | failed
    started_at: str
    completed_at: Optional[str]
    approved_count: Optional[int]
    error: Optional[str]


# ── Background pipeline runner ─────────────────────────────────────────────────

async def _run_pipeline_async(run_id: str, request: RunRequest):
    """Runs the crew pipeline in a background task."""
    runs[run_id]["status"] = "running"
    try:
        # Import here to avoid blocking startup
        from crew import build_crew

        loop = asyncio.get_event_loop()
        crew, tasks = await loop.run_in_executor(None, build_crew, request.search_query)
        raw = await loop.run_in_executor(None, crew.kickoff)

        # Parse audit report
        audit_raw = ""
        if hasattr(tasks[3], "output") and tasks[3].output:
            audit_raw = tasks[3].output.raw_output or ""

        try:
            clean = audit_raw.strip().lstrip("```json").rstrip("```").strip()
            audit = json.loads(clean)
        except Exception:
            audit = {"approved": [], "rejected": [], "_raw": audit_raw[:300]}

        runs[run_id].update(
            {
                "status": "awaiting_approval",
                "scout": getattr(tasks[0].output, "raw_output", "") if hasattr(tasks[0], "output") else "",
                "research": getattr(tasks[1].output, "raw_output", "") if hasattr(tasks[1], "output") else "",
                "drafts": getattr(tasks[2].output, "raw_output", "") if hasattr(tasks[2], "output") else "",
                "audit": audit,
            }
        )

    except Exception as e:
        runs[run_id]["status"] = "failed"
        runs[run_id]["error"] = str(e)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/run", response_model=RunStatus)
async def start_run(request: RunRequest):
    """Start a new pipeline run."""
    run_id = str(uuid.uuid4())[:8]
    runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "approved_count": None,
        "error": None,
        "request": request.dict(),
    }
    asyncio.create_task(_run_pipeline_async(run_id, request))
    return RunStatus(**{k: runs[run_id].get(k) for k in RunStatus.__fields__})


@app.get("/status/{run_id}", response_model=RunStatus)
def get_status(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, f"Run {run_id} not found")
    r = runs[run_id]
    return RunStatus(**{k: r.get(k) for k in RunStatus.__fields__})


@app.get("/results/{run_id}")
def get_results(run_id: str):
    """Get the full pipeline results for a run."""
    if run_id not in runs:
        raise HTTPException(404, f"Run {run_id} not found")
    r = runs[run_id]
    if r["status"] not in ("awaiting_approval", "complete"):
        raise HTTPException(400, f"Run is not yet ready (status: {r['status']})")
    return {
        "audit_report": r.get("audit"),
        "approved_emails": r.get("approved_emails", []),
        "schedule_result": r.get("schedule_result", ""),
    }


@app.post("/approve/{run_id}")
async def submit_approvals(run_id: str, request: ApprovalRequest):
    """
    Submit human approval decisions.
    This is the API-level human-in-the-loop gate.
    """
    if run_id not in runs:
        raise HTTPException(404, f"Run {run_id} not found")
    r = runs[run_id]
    if r["status"] != "awaiting_approval":
        raise HTTPException(400, f"Run is not awaiting approval (status: {r['status']})")

    audit = r.get("audit", {})
    approved_drafts = audit.get("approved", [])

    final_approved = []
    for i in request.approved_indices:
        if i < len(approved_drafts):
            email = approved_drafts[i].copy()
            # Apply any edits
            if request.edited_bodies and i in request.edited_bodies:
                email["body"] = request.edited_bodies[i]
            final_approved.append(email)

    r["approved_emails"] = final_approved

    # Run scheduler in background
    if final_approved:
        async def schedule():
            from crew import build_scheduler_agent
            from crewai import Task, Crew, Process
            import asyncio

            scheduler = build_scheduler_agent()
            task = Task(
                description=(
                    f"Schedule follow-up calendar events:\n{json.dumps(final_approved, indent=2)}"
                ),
                expected_output="Scheduling summary.",
                agent=scheduler,
            )
            crew = Crew(agents=[scheduler], tasks=[task], process=Process.sequential)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
            r["schedule_result"] = str(result)
            r["status"] = "complete"
            r["completed_at"] = datetime.utcnow().isoformat()
            r["approved_count"] = len(final_approved)

        asyncio.create_task(schedule())
    else:
        r["status"] = "complete"
        r["completed_at"] = datetime.utcnow().isoformat()
        r["approved_count"] = 0

    return {"message": f"{len(final_approved)} email(s) approved", "run_id": run_id}


@app.get("/runs")
def list_runs():
    """List all pipeline runs."""
    return [
        {
            "run_id": r["run_id"],
            "status": r["status"],
            "started_at": r["started_at"],
            "approved_count": r.get("approved_count"),
        }
        for r in runs.values()
    ]
