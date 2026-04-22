"""
tools/calendar_tool.py
Wraps Google Calendar API so the Scheduler agent can create follow-up events.

Setup (one-time):
  1. Go to console.cloud.google.com → Create project → Enable "Google Calendar API"
  2. Create OAuth 2.0 credentials (Desktop app) → download client_secret.json
  3. Run `python tools/calendar_tool.py --auth` once to generate token.json
  4. Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

TOKEN_FILE = Path("token.json")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_google_service(service_name: str, version: str):
    """Build and return an authenticated Google API service client."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Install google packages: pip install google-auth google-auth-oauthlib "
            "google-auth-httplib2 google-api-python-client"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # In production this would redirect to OAuth flow
            raise RuntimeError(
                "Google credentials not found. Run: python tools/calendar_tool.py --auth"
            )
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build(service_name, version, credentials=creds)


# ── Input Schemas ─────────────────────────────────────────────────────────────

class CreateCalendarEventInput(BaseModel):
    title: str = Field(..., description="Event title.")
    description: str = Field("", description="Event description / notes.")
    attendee_email: Optional[str] = Field(None, description="Attendee email address.")
    days_from_now: int = Field(7, description="Schedule the event N days from today.")
    duration_minutes: int = Field(30, description="Duration of the event in minutes.")


class ListUpcomingEventsInput(BaseModel):
    max_results: int = Field(10, description="Max number of events to return.")


# ── Tools ─────────────────────────────────────────────────────────────────────

class CreateCalendarEventTool(BaseTool):
    """Create a Google Calendar follow-up event."""

    name: str = "create_calendar_event"
    description: str = (
        "Schedule a follow-up meeting or reminder in Google Calendar. "
        "Provide a title, description, attendee email, and when to schedule it."
    )
    args_schema: Type[BaseModel] = CreateCalendarEventInput

    def _run(
        self,
        title: str,
        description: str = "",
        attendee_email: Optional[str] = None,
        days_from_now: int = 7,
        duration_minutes: int = 30,
    ) -> str:
        try:
            service = _get_google_service("calendar", "v3")
        except (ImportError, RuntimeError) as e:
            # Graceful degradation for demo mode (no real OAuth token)
            return json.dumps(
                {
                    "status": "DEMO_MODE",
                    "message": str(e),
                    "would_create": {
                        "title": title,
                        "description": description,
                        "attendee": attendee_email,
                        "scheduled_in_days": days_from_now,
                        "duration_minutes": duration_minutes,
                    },
                },
                indent=2,
            )

        start = datetime.utcnow() + timedelta(days=days_from_now)
        end = start + timedelta(minutes=duration_minutes)

        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat() + "Z", "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat() + "Z", "timeZone": "UTC"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        if attendee_email:
            event_body["attendees"] = [{"email": attendee_email}]

        event = (
            service.events()
            .insert(calendarId="primary", body=event_body, sendUpdates="all")
            .execute()
        )

        return json.dumps(
            {
                "status": "created",
                "event_id": event.get("id"),
                "html_link": event.get("htmlLink"),
                "summary": event.get("summary"),
                "start": event["start"].get("dateTime"),
            },
            indent=2,
        )

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class ListUpcomingEventsTool(BaseTool):
    """List upcoming Google Calendar events."""

    name: str = "list_calendar_events"
    description: str = "List upcoming events from Google Calendar."
    args_schema: Type[BaseModel] = ListUpcomingEventsInput

    def _run(self, max_results: int = 10) -> str:
        try:
            service = _get_google_service("calendar", "v3")
            now = datetime.utcnow().isoformat() + "Z"
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            return json.dumps(
                [
                    {
                        "summary": e.get("summary"),
                        "start": e["start"].get("dateTime", e["start"].get("date")),
                        "id": e.get("id"),
                    }
                    for e in events
                ],
                indent=2,
            )
        except (ImportError, RuntimeError) as e:
            return f"DEMO_MODE: {e}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


# ── CLI auth helper ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if "--auth" in sys.argv:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"✅  Token saved to {TOKEN_FILE}")
