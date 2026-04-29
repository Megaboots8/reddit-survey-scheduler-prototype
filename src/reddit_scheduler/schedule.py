"""
Posting schedule resolver.

Each study declares a posting_plan: per-subreddit weekly time slots in a
specific timezone. find_due_slots() returns the (subreddit, flair, slot)
tuples for a given study that are "due" right now (within a configurable
window around the slot time).

The scheduler only attempts a post when a slot is due. This is what
prevents the scheduler from posting more frequently than the declared
schedule, regardless of how often it is invoked.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DAY_INDEX = {
    "mon": 0, "monday": 0,
    "tue": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


def find_due_slots(
    study: dict,
    now_utc: datetime,
    window_minutes: int = 30,
) -> list[dict]:
    """Return all subreddit slots for this study that are due at now_utc.

    A slot is "due" if abs(now - slot_today) <= window_minutes.

    Returns a list of dicts with keys: subreddit, flair, scheduled_iso.
    Returns an empty list if nothing is due — caller should skip the study.
    """
    due: list[dict] = []
    for plan_entry in study.get("posting_plan", []):
        tz = ZoneInfo(plan_entry.get("timezone", "UTC"))
        local_now = now_utc.astimezone(tz)

        match = _first_due_slot(plan_entry.get("slots", []), local_now, window_minutes)
        if match is None:
            continue

        due.append(
            {
                "subreddit": plan_entry["subreddit"],
                "flair": plan_entry.get("flair", ""),
                "scheduled_iso": match.isoformat(),
                "timezone": str(tz),
            }
        )
    return due


def _first_due_slot(
    slots: list[dict],
    local_now: datetime,
    window_minutes: int,
) -> datetime | None:
    """Return the slot's local datetime if it falls within the window of now."""
    for slot in slots:
        target_dow = DAY_INDEX.get(str(slot.get("day", "")).lower())
        if target_dow is None or target_dow != local_now.weekday():
            continue

        hour, minute = _parse_hhmm(slot.get("time", ""))
        if hour is None:
            continue

        slot_dt = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if abs(local_now - slot_dt) <= timedelta(minutes=window_minutes):
            return slot_dt
    return None


def _parse_hhmm(value: str) -> tuple[int | None, int | None]:
    try:
        h_str, m_str = value.split(":")
        return int(h_str), int(m_str)
    except (ValueError, AttributeError):
        return None, None
