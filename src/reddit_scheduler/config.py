"""Load and validate scheduler configuration from a YAML file."""

from __future__ import annotations

from pathlib import Path

import yaml


def load(path: str | Path) -> dict:
    """Load config YAML and return the parsed dict.

    Raises ValueError with a descriptive message if required top-level keys
    are missing so problems are caught at startup, not mid-run.
    """
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    required = ["allowed_subreddits", "global_limits", "per_subreddit", "studies"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")

    if not data.get("allowed_subreddits"):
        raise ValueError("allowed_subreddits must contain at least one entry.")

    return data
