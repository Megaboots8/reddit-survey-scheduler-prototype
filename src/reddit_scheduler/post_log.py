"""Append-only CSV post log.

Records every scheduler decision: skips, declines, and approved-but-disabled
posts. After Reddit API approval, will also record real Reddit post IDs.

Each row also carries the *aggregate* response/completion counts at the
moment of decision, so we can track how many participants each post brings
in. Aggregate counts only — no individual respondent data ever lands in
the log.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = [
    "timestamp_iso",
    "study_id",
    "subreddit",
    "action",
    "reason",
    "approver",
    "reddit_post_id",
    "response_count",
    "completion_count",
    "data_source",
]


def load(path: str | Path) -> list[dict]:
    """Read all rows from the log file. Returns an empty list if the file does not exist."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def append(
    path: str | Path,
    *,
    study_id: str,
    subreddit: str,
    action: str,
    reason: str,
    approver: str = "",
    reddit_post_id: str = "",
    response_count: str | int = "",
    completion_count: str | int = "",
    data_source: str = "",
) -> None:
    """Append one row to the log file, creating it with a header if it does not exist."""
    p = Path(path)
    write_header = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_iso": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "study_id": study_id,
                "subreddit": subreddit,
                "action": action,
                "reason": reason,
                "approver": approver,
                "reddit_post_id": reddit_post_id,
                "response_count": response_count,
                "completion_count": completion_count,
                "data_source": data_source,
            }
        )
