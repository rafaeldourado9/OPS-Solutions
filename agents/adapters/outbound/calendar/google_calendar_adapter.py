"""
GoogleCalendarAdapter — CalendarPort implementation using Google Calendar API v3.

Setup:
1. Create a Google Cloud project and enable Calendar API.
2. Create a Service Account and download credentials JSON.
3. Share the target Google Calendar with the service account email (Editor permission).
4. Set env vars:
   GOOGLE_CALENDAR_CREDENTIALS_FILE=/path/to/credentials.json
   GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com

Dependencies: google-auth google-api-python-client
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.ports.calendar_port import CalendarEvent, CalendarPort

logger = logging.getLogger(__name__)


class GoogleCalendarAdapter(CalendarPort):
    """
    CalendarPort implementation for Google Calendar.

    Uses a service account for authentication — no OAuth interactive flow needed.
    """

    def __init__(self, credentials_file: str, calendar_id: str) -> None:
        self._credentials_file = credentials_file
        self._calendar_id = calendar_id
        self._service = None

    def _get_service(self):
        """Lazy-init the Google Calendar service (sync, called once)."""
        if self._service is not None:
            return self._service
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/calendar"]
            creds = service_account.Credentials.from_service_account_file(
                self._credentials_file, scopes=scopes
            )
            self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        except Exception:
            logger.exception("Failed to initialize Google Calendar service")
            raise
        return self._service

    async def create_event(self, event: CalendarEvent) -> Optional[str]:
        """Create a Google Calendar event and return the event ID."""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._create_event_sync, event)
        except Exception:
            logger.exception("Failed to create Google Calendar event: %s", event.title)
            return None

    def _create_event_sync(self, event: CalendarEvent) -> Optional[str]:
        try:
            service = self._get_service()
            # Build reminder overrides (2 days = 2880 min before, 1 hour = 60 min before)
            overrides = [{"method": "popup", "minutes": m} for m in event.reminder_minutes]
            body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start.isoformat(),
                    "timeZone": "America/Sao_Paulo",
                },
                "end": {
                    "dateTime": event.end.isoformat(),
                    "timeZone": "America/Sao_Paulo",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": overrides,
                },
            }
            result = service.events().insert(calendarId=self._calendar_id, body=body).execute()
            event_id = result.get("id")
            logger.info("Created Google Calendar event: %s (id=%s)", event.title, event_id)
            return event_id
        except Exception:
            logger.exception("Google Calendar create_event_sync failed")
            return None

    async def list_upcoming_events(self, days_ahead: int = 7) -> list[CalendarEvent]:
        """List events in the next N days from Google Calendar."""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._list_events_sync, days_ahead)
        except Exception:
            logger.exception("Failed to list Google Calendar events")
            return []

    def _list_events_sync(self, days_ahead: int) -> list[CalendarEvent]:
        try:
            service = self._get_service()
            now = datetime.now(timezone.utc)
            time_max = now + timedelta(days=days_ahead)
            result = service.events().list(
                calendarId=self._calendar_id,
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = []
            for item in result.get("items", []):
                start_str = item["start"].get("dateTime") or item["start"].get("date")
                end_str = item["end"].get("dateTime") or item["end"].get("date")
                try:
                    start = datetime.fromisoformat(start_str)
                    end = datetime.fromisoformat(end_str)
                except Exception:
                    continue
                events.append(CalendarEvent(
                    title=item.get("summary", "Evento"),
                    start=start,
                    end=end,
                    description=item.get("description", ""),
                    event_id=item.get("id"),
                ))
            return events
        except Exception:
            logger.exception("Google Calendar list_events_sync failed")
            return []

    async def delete_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event by ID."""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._delete_event_sync, event_id)
        except Exception:
            logger.exception("Failed to delete Google Calendar event: %s", event_id)
            return False

    def _delete_event_sync(self, event_id: str) -> bool:
        try:
            service = self._get_service()
            service.events().delete(calendarId=self._calendar_id, eventId=event_id).execute()
            return True
        except Exception:
            logger.exception("Google Calendar delete_event_sync failed")
            return False
