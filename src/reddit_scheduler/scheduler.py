"""
Main scheduler flow.

For each active study x allowed subreddit, runs safety gates in order,
asks for human approval, then calls reddit_client.submit_post() — which
is currently gated off pending Reddit Data API approval.
"""

from __future__ import annotations

from . import approval, post_log, safety_checks
from .reddit_client import PostingDisabledError, submit_post


def run(cfg: dict, log_path: str) -> None:
    """Execute one scheduling pass: check all gates, prompt for approval, attempt post."""
    rows = post_log.load(log_path)

    allowed_subreddits: list[str] = cfg["allowed_subreddits"]
    daily_limit: int = cfg["global_limits"]["daily_post_limit"]
    account_gap_hours: int = cfg["global_limits"]["per_account_min_gap_hours"]
    subreddit_cooldown_hours: int = cfg["per_subreddit"]["cooldown_hours"]
    dup_window_days: int = cfg.get("duplicate_risk", {}).get("similar_title_window_days", 30)
    studies: list[dict] = cfg.get("studies", [])

    for study in studies:
        study_id = study.get("id", "unknown")

        if not safety_checks.is_study_active(study):
            print(f"[skip] {study_id}: study not active")
            continue

        missing = safety_checks.missing_required_fields(study)
        if missing:
            print(f"[skip] {study_id}: missing required fields: {missing}")
            continue

        for subreddit in allowed_subreddits:

            # Gate 1 — allowlist
            if not safety_checks.is_subreddit_allowed(subreddit, allowed_subreddits):
                _log_skip(log_path, study_id, subreddit, "subreddit_not_in_allowlist")
                continue

            # Gate 2 — per-subreddit cooldown
            if not safety_checks.respects_subreddit_cooldown(subreddit, rows, subreddit_cooldown_hours):
                print(f"[skip] {study_id} -> r/{subreddit}: subreddit cooldown active")
                _log_skip(log_path, study_id, subreddit, "per_subreddit_cooldown_active")
                rows = post_log.load(log_path)
                continue

            # Gate 3 — per-account cooldown
            if not safety_checks.respects_account_cooldown(rows, account_gap_hours):
                print(f"[skip] {study_id} -> r/{subreddit}: account-level cooldown active")
                _log_skip(log_path, study_id, subreddit, "per_account_cooldown_active")
                rows = post_log.load(log_path)
                continue

            # Gate 4 — daily post limit
            if not safety_checks.under_daily_post_limit(rows, daily_limit):
                print(f"[skip] {study_id} -> r/{subreddit}: daily post limit reached")
                _log_skip(log_path, study_id, subreddit, "daily_post_limit_reached")
                rows = post_log.load(log_path)
                continue

            # Gate 5 — duplicate risk
            if not safety_checks.low_duplicate_risk(study, subreddit, rows, dup_window_days):
                print(f"[skip] {study_id} -> r/{subreddit}: duplicate risk (recent post within window)")
                _log_skip(log_path, study_id, subreddit, "duplicate_risk_within_window")
                rows = post_log.load(log_path)
                continue

            # Gate 6 — human approval
            title = study["title"]
            body = study.get("post_template", "").format(**study)
            preview = f"Subreddit : r/{subreddit}\nTitle     : {title}\n\n{body}"

            approved, approver = approval.confirm_post(preview)
            if not approved:
                print(f"[declined] {study_id} -> r/{subreddit}: declined by operator")
                post_log.append(log_path, study_id, subreddit, "declined_by_human", "human_chose_not_to_post")
                rows = post_log.load(log_path)
                continue

            # Attempt submission (currently gated)
            try:
                post_id = submit_post(subreddit, title, body)
                print(f"[posted] {study_id} -> r/{subreddit}: post ID {post_id}")
                post_log.append(log_path, study_id, subreddit, "posted", "success", approver, post_id)
            except PostingDisabledError as e:
                print(f"[approved_disabled] {study_id} -> r/{subreddit}: {e}")
                post_log.append(
                    log_path, study_id, subreddit,
                    "approved_disabled", "posting_disabled_pending_api_approval",
                    approver,
                )

            rows = post_log.load(log_path)


def _log_skip(log_path: str, study_id: str, subreddit: str, reason: str) -> None:
    post_log.append(log_path, study_id, subreddit, "skipped", reason)
