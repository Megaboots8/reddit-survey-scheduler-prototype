"""
Main scheduler flow.

For each active study, the scheduler:

  1. Checks the posting schedule. Only proceeds for subreddits whose
     time slot is due *now* (within the configured window). Studies
     with no due slots are skipped entirely.
  2. Reads aggregate study status (response and completion counts) from
     the configured data source. Aggregate-only — never individual rows.
  3. Runs safety gates in order: allowlist, missing required fields,
     per-subreddit cooldown, per-account cooldown, daily cap, duplicate
     risk.
  4. Asks for human approval, showing a full post preview.
  5. On approval, attempts reddit_client.submit_post() — currently gated
     off, raises PostingDisabledError, logged as 'approved_disabled'.

Every decision (skip, decline, approved-disabled) appends a row to the
post log so the full history of scheduler activity is auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import approval, post_log, safety_checks, schedule, study_status
from .reddit_client import PostingDisabledError, submit_post


def run(cfg: dict, log_path: str) -> None:
    """Execute one scheduling pass."""
    rows = post_log.load(log_path)

    allowed_subreddits: list[str] = cfg["allowed_subreddits"]
    daily_limit: int = cfg["global_limits"]["daily_post_limit"]
    account_gap_minutes: int = cfg["global_limits"]["per_account_min_gap_minutes"]
    subreddit_cooldown_hours: int = cfg["per_subreddit"]["cooldown_hours"]
    dup_window_days: int = cfg.get("duplicate_risk", {}).get("similar_title_window_days", 30)
    schedule_window: int = cfg.get("schedule_window_minutes", 30)
    studies: list[dict] = cfg.get("studies", [])
    now_utc = datetime.now(tz=timezone.utc)

    for study in studies:
        study_id = study.get("id", "unknown")

        if not safety_checks.is_study_active(study):
            print(f"[skip] {study_id}: study not active")
            continue

        missing = safety_checks.missing_required_fields(study)
        if missing:
            print(f"[skip] {study_id}: missing required fields: {missing}")
            continue

        # Schedule check — only continue for slots that are due now.
        due_slots = schedule.find_due_slots(study, now_utc, schedule_window)
        if not due_slots:
            print(f"[skip] {study_id}: no scheduled slot due now")
            continue

        # Aggregate study status (mock while integrations disabled).
        status = study_status.get_status(study)
        print(
            f"[status] {study_id}: source={status.source} "
            f"responses={status.response_count} complete={status.completion_count}"
        )

        for slot in due_slots:
            subreddit = slot["subreddit"]
            flair = slot["flair"]

            # Gate 1 — allowlist
            if not safety_checks.is_subreddit_allowed(subreddit, allowed_subreddits):
                _log(log_path, study_id, subreddit, "skipped", "subreddit_not_in_allowlist", status=status)
                continue

            # Gate 2 — per-subreddit cooldown
            if not safety_checks.respects_subreddit_cooldown(subreddit, rows, subreddit_cooldown_hours):
                print(f"[skip] {study_id} -> r/{subreddit}: subreddit cooldown active")
                _log(log_path, study_id, subreddit, "skipped", "per_subreddit_cooldown_active", status=status)
                rows = post_log.load(log_path)
                continue

            # Gate 3 — per-account cooldown
            if not safety_checks.respects_account_cooldown(rows, account_gap_minutes):
                print(f"[skip] {study_id} -> r/{subreddit}: account-level cooldown active")
                _log(log_path, study_id, subreddit, "skipped", "per_account_cooldown_active", status=status)
                rows = post_log.load(log_path)
                continue

            # Gate 4 — daily post limit
            if not safety_checks.under_daily_post_limit(rows, daily_limit):
                print(f"[skip] {study_id} -> r/{subreddit}: daily post limit reached")
                _log(log_path, study_id, subreddit, "skipped", "daily_post_limit_reached", status=status)
                rows = post_log.load(log_path)
                continue

            # Gate 5 — duplicate risk
            if not safety_checks.low_duplicate_risk(study, subreddit, rows, dup_window_days):
                print(f"[skip] {study_id} -> r/{subreddit}: duplicate risk (recent post within window)")
                _log(log_path, study_id, subreddit, "skipped", "duplicate_risk_within_window", status=status)
                rows = post_log.load(log_path)
                continue

            # Gate 6 — human approval
            title = study["title"]
            body = study.get("post_template", "").format(**study)
            preview = (
                f"Subreddit : r/{subreddit}\n"
                f"Flair     : {flair}\n"
                f"Title     : {title}\n"
                f"Aggregate : {status.response_count} responses, "
                f"{status.completion_count} complete (source: {status.source})\n\n"
                f"{body}"
            )

            approved, approver = approval.confirm_post(preview)
            if not approved:
                print(f"[declined] {study_id} -> r/{subreddit}: declined by operator")
                _log(log_path, study_id, subreddit, "declined_by_human", "human_chose_not_to_post", status=status)
                rows = post_log.load(log_path)
                continue

            # Attempt submission (currently gated)
            try:
                post_id = submit_post(subreddit, title, body, flair=flair)
                print(f"[posted] {study_id} -> r/{subreddit}: post ID {post_id}")
                _log(log_path, study_id, subreddit, "posted", "success",
                     approver=approver, reddit_post_id=post_id, status=status)
            except PostingDisabledError as e:
                print(f"[approved_disabled] {study_id} -> r/{subreddit}: {e}")
                _log(log_path, study_id, subreddit, "approved_disabled",
                     "posting_disabled_pending_api_approval",
                     approver=approver, status=status)

            rows = post_log.load(log_path)


def _log(
    log_path: str,
    study_id: str,
    subreddit: str,
    action: str,
    reason: str,
    *,
    approver: str = "",
    reddit_post_id: str = "",
    status: study_status.StudyStatus | None = None,
) -> None:
    response_count = status.response_count if status else ""
    completion_count = status.completion_count if status else ""
    data_source = status.source if status else ""
    post_log.append(
        log_path,
        study_id=study_id,
        subreddit=subreddit,
        action=action,
        reason=reason,
        approver=approver,
        reddit_post_id=reddit_post_id,
        response_count=response_count,
        completion_count=completion_count,
        data_source=data_source,
    )
