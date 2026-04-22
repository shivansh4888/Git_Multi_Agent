from pathlib import Path
import sys
import asyncio
from datetime import datetime
import uuid

import fastapi.testclient
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _SimpleResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class SimpleTestClient:
    def __init__(self, app):
        self.app = app

    def get(self, path: str):
        from ui import api

        try:
            if path == "/health":
                return _SimpleResponse(200, api.health())
            if path.startswith("/status/"):
                run_id = path.rsplit("/", 1)[-1]
                result = api.get_status(run_id)
                return _SimpleResponse(200, result.model_dump())
            if path.startswith("/results/"):
                run_id = path.rsplit("/", 1)[-1]
                result = api.get_results(run_id)
                return _SimpleResponse(200, result)
        except HTTPException as exc:
            return _SimpleResponse(exc.status_code, {"detail": exc.detail})

        return _SimpleResponse(404, {"detail": "Not found"})

    def post(self, path: str, json: dict):
        from ui import api

        try:
            if path == "/run":
                request = api.RunRequest(**json)
                run_id = str(uuid.uuid4())[:8]
                api.runs[run_id] = {
                    "run_id": run_id,
                    "status": "queued",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": None,
                    "approved_count": None,
                    "error": None,
                    "request": request.model_dump(),
                }
                result = api.RunStatus(
                    **{k: api.runs[run_id].get(k) for k in api.RunStatus.model_fields}
                )
                return _SimpleResponse(200, result.model_dump())
            if path.startswith("/approve/"):
                run_id = path.rsplit("/", 1)[-1]
                request = api.ApprovalRequest(**json)
                result = asyncio.run(api.submit_approvals(run_id, request))
                return _SimpleResponse(200, result)
        except HTTPException as exc:
            return _SimpleResponse(exc.status_code, {"detail": exc.detail})

        return _SimpleResponse(404, {"detail": "Not found"})


fastapi.testclient.TestClient = SimpleTestClient
