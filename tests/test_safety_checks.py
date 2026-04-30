"""Unit tests for safety_checks.py.

These tests are pure: they construct fake log rows in memory and call the
guardrail functions directly. They never touch the network, never import
praw, and never read real config or credentials.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from reddit_scheduler import safety_checks


ALLOWLIST = ["SampleSize", "TakeMySurvey"]


def _row(
    *,
    minutes_ago: int = 0,
    days_ago: int = 0,
    subreddit: str = "SampleSize",
    study_id: str = "study_a",
    action: str = "posted",
) -> dict:
    """Build a fake post-log row with a timestamp offset from 'now'."""
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago, minutes=minutes_ago)
    return {
        "timestamp_iso": ts.isoformat(),
        "subreddit": subreddit,
        "study_id": study_id,
        "action": action,
    }


# is_subreddit_allowed --------------------------------------------------------


def test_disallows_non_allowlisted_subreddit():
    assert safety_checks.is_subreddit_allowed("SampleSize", ALLOWLIST) is True
    assert safety_checks.is_subreddit_allowed("AskReddit", ALLOWLIST) is False


def test_empty_allowlist_blocks_everything():
    assert safety_checks.is_subreddit_allowed("SampleSize", []) is False


# is_study_active -------------------------------------------------------------


def test_requires_active_study():
    assert safety_checks.is_study_active({"active": True}) is True
    assert safety_checks.is_study_active({"active": False}) is False
    assert safety_checks.is_study_active({}) is False


# missing_required_fields -----------------------------------------------------


def test_missing_required_fields_reports_absent_and_empty():
    study = {
        "required_fields": ["title", "body", "url"],
        "title": "Hello",
        "body": "",
    }
    missing = safety_checks.missing_required_fields(study)
    assert set(missing) == {"body", "url"}


def test_missing_required_fields_empty_when_all_present():
    study = {
        "required_fields": ["title"],
        "title": "Hello",
    }
    assert safety_checks.missing_required_fields(study) == []


# respects_subreddit_cooldown -------------------------------------------------


def test_subreddit_cooldown_blocks_recent_post():
    log = [_row(minutes_ago=60, subreddit="SampleSize")]
    assert (
        safety_checks.respects_subreddit_cooldown("SampleSize", log, cooldown_hours=25)
        is False
    )


def test_subreddit_cooldown_blocks_any_study_in_same_subreddit():
    """The cooldown is per subreddit, not per study."""
    log = [_row(minutes_ago=60, subreddit="SampleSize", study_id="study_a")]
    assert (
        safety_checks.respects_subreddit_cooldown("SampleSize", log, cooldown_hours=25)
        is False
    )


def test_subreddit_cooldown_passes_after_window():
    log = [_row(days_ago=2, subreddit="SampleSize")]
    assert (
        safety_checks.respects_subreddit_cooldown("SampleSize", log, cooldown_hours=25)
        is True
    )


def test_subreddit_cooldown_ignores_other_subreddits():
    log = [_row(minutes_ago=10, subreddit="TakeMySurvey")]
    assert (
        safety_checks.respects_subreddit_cooldown("SampleSize", log, cooldown_hours=25)
        is True
    )


# respects_account_cooldown ---------------------------------------------------


def test_account_cooldown_blocks_rapid_posts_across_subreddits():
    log = [_row(minutes_ago=10, subreddit="TakeMySurvey")]
    assert safety_checks.respects_account_cooldown(log, min_gap_minutes=60) is False


def test_account_cooldown_passes_after_gap():
    log = [_row(minutes_ago=120, subreddit="TakeMySurvey")]
    assert safety_checks.respects_account_cooldown(log, min_gap_minutes=60) is True


# under_daily_post_limit ------------------------------------------------------


def test_blocks_daily_post_limit_when_at_cap():
    log = [_row(minutes_ago=5, subreddit="SampleSize")]
    assert safety_checks.under_daily_post_limit(log, limit=1) is False


def test_under_daily_post_limit_with_no_posts_today():
    log = [_row(days_ago=2, subreddit="SampleSize")]
    assert safety_checks.under_daily_post_limit(log, limit=1) is True


def test_daily_limit_counts_only_posted_actions():
    log = [
        _row(minutes_ago=5, action="skipped_cooldown"),
        _row(minutes_ago=5, action="approved_disabled"),
    ]
    assert safety_checks.under_daily_post_limit(log, limit=1) is False
    assert safety_checks.under_daily_post_limit(log, limit=2) is True


# low_duplicate_risk ----------------------------------------------------------


def test_blocks_duplicate_study_within_window():
    log = [_row(days_ago=10, subreddit="SampleSize", study_id="study_a")]
    study = {"id": "study_a"}
    assert (
        safety_checks.low_duplicate_risk(study, "SampleSize", log, window_days=30)
        is False
    )


def test_duplicate_check_allows_different_study_in_same_subreddit():
    log = [_row(days_ago=2, subreddit="SampleSize", study_id="study_a")]
    study = {"id": "study_b"}
    assert (
        safety_checks.low_duplicate_risk(study, "SampleSize", log, window_days=30)
        is True
    )


def test_duplicate_check_passes_after_window():
    log = [_row(days_ago=45, subreddit="SampleSize", study_id="study_a")]
    study = {"id": "study_a"}
    assert (
        safety_checks.low_duplicate_risk(study, "SampleSize", log, window_days=30)
        is True
    )
