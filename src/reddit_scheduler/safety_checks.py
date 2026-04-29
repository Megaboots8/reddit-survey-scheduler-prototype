"""
Safety guardrails for the Reddit survey post scheduler.

All functions are pure: they take explicit arguments and return a bool or list.
None of them read from Reddit, write to Reddit, or touch the network.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def is_subreddit_allowed(subreddit: str, allowlist: list[str]) -> bool:
    """Return True only if subreddit appears in the configured allowlist.

    The allowlist is the sole mechanism that prevents the scheduler from
    posting to arbitrary subreddits. It must be edited deliberately in the
    config file — it cannot be overridden at runtime.
    """
    return subreddit in allowlist


def is_study_active(study: dict) -> bool:
    """Return True if the study is marked active in config.

    Studies are inactive by default and must be explicitly enabled.
    """
    return bool(study.get("active", False))


def missing_required_fields(study: dict) -> list[str]:
    """Return a list of required field names that are absent or empty.

    An empty list means all required fields are present and non-empty.
    The required_fields list is defined per-study in the config so each
    study can declare exactly what its post needs.
    """
    required = study.get("required_fields", [])
    return [field for field in required if not study.get(field)]


def respects_subreddit_cooldown(
    subreddit: str,
    log_rows: list[dict],
    cooldown_hours: int,
) -> bool:
    """Return True if enough time has passed since the last post to this subreddit.

    Prevents the account from posting the same study to the same subreddit
    more frequently than once per cooldown window (default: 1 week).
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=cooldown_hours)
    for row in log_rows:
        if row.get("subreddit") != subreddit:
            continue
        if row.get("action") not in ("posted", "approved_disabled"):
            continue
        ts = _parse_ts(row.get("timestamp_iso", ""))
        if ts and ts > cutoff:
            return False
    return True


def respects_account_cooldown(log_rows: list[dict], min_gap_hours: int) -> bool:
    """Return True if enough time has passed since the last post from this account.

    Prevents rapid-fire posting across all subreddits regardless of
    per-subreddit cooldowns.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=min_gap_hours)
    for row in log_rows:
        if row.get("action") not in ("posted", "approved_disabled"):
            continue
        ts = _parse_ts(row.get("timestamp_iso", ""))
        if ts and ts > cutoff:
            return False
    return True


def under_daily_post_limit(log_rows: list[dict], limit: int) -> bool:
    """Return True if the number of posts today is below the daily cap.

    Counts only rows with action 'posted' or 'approved_disabled' from the
    current UTC calendar day.
    """
    today = datetime.now(tz=timezone.utc).date()
    count = 0
    for row in log_rows:
        if row.get("action") not in ("posted", "approved_disabled"):
            continue
        ts = _parse_ts(row.get("timestamp_iso", ""))
        if ts and ts.date() == today:
            count += 1
    return count < limit


def low_duplicate_risk(
    study: dict,
    subreddit: str,
    log_rows: list[dict],
    window_days: int,
) -> bool:
    """Return True if no similar post was made to this subreddit within the window.

    Checks for an exact study_id match in recent log rows for this subreddit.
    Prevents reposting the same survey before the previous post has aged out.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=window_days)
    study_id = study.get("id", "")
    for row in log_rows:
        if row.get("subreddit") != subreddit:
            continue
        if row.get("study_id") != study_id:
            continue
        if row.get("action") not in ("posted", "approved_disabled"):
            continue
        ts = _parse_ts(row.get("timestamp_iso", ""))
        if ts and ts > cutoff:
            return False
    return True


def _parse_ts(value: str) -> datetime | None:
    """Parse an ISO 8601 timestamp string; return None on failure."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
