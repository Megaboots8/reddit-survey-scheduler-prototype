# Reddit Survey Scheduler Prototype

> **Status:** Skeleton / pre-implementation.
> Actual Reddit submission is **disabled** until Reddit Data API access is approved.
> See [`src/reddit_scheduler/reddit_client.py`](src/reddit_scheduler/reddit_client.py) — `POSTING_ENABLED = False`.

---

## Purpose

This is a human-approved scheduler for posting survey recruitment links to a small, curated allowlist of survey-friendly Reddit communities. It is designed for academic and marketing research studies that require participant recruitment.

All posts are submitted from the dedicated account `u/PerceptionStudies`. Every post requires explicit human approval before the scheduler will attempt submission. The scheduler enforces strict cooldowns, daily caps, and an allowlist so that the account cannot be used to spam any subreddit.

Studies include an IRB statement and eligibility criteria in every post.

---

## What it does

1. Loads study metadata and scheduler config from `examples/config.example.yaml`.
2. For each active study and each allowed subreddit, runs the following gates **in order**:
   - Subreddit is in the allowlist
   - Study is marked active and has all required fields
   - Per-subreddit cooldown has elapsed
   - Per-account minimum gap between posts has elapsed
   - Daily post cap has not been reached
   - No duplicate or near-duplicate post within the lookback window
3. Presents a preview of the post and asks for **human approval** (y/N in the terminal).
4. If approved, calls `reddit_client.submit_post()` — which is currently **gated off** and logs `approved_disabled` until API access is granted.
5. Appends a structured row to the post log (`post_log.csv`) regardless of outcome.

---

## What it does NOT do

- Does **not** vote, upvote, or downvote any post or comment.
- Does **not** send private messages or chat messages to any Reddit user.
- Does **not** post automated comments or replies.
- Does **not** scrape Reddit user profiles, post histories, or any user data.
- Does **not** manipulate karma.
- Does **not** evade bans or bypass subreddit rules.
- Does **not** post to subreddits outside the explicit allowlist in config.
- Does **not** post without a human reviewing and approving each post first.
- Does **not** interact with Google Sheets, MySQL, or any external database. This prototype is standalone.

---

## Account and allowlist

**Posting account:** `u/PerceptionStudies` (dedicated research account, no other use)

**Allowed subreddits** (defined in config, not hardcoded):
- `r/SampleSize` — explicitly permits survey posts per subreddit rules
- `r/TakeMySurvey` — explicitly permits survey posts per subreddit rules

Adding or removing a subreddit requires editing `allowed_subreddits` in the config file. The code will refuse to post to any subreddit not on that list.

---

## Safety checks

Each gate is implemented as a standalone pure function in [`src/reddit_scheduler/safety_checks.py`](src/reddit_scheduler/safety_checks.py):

| Function | Guard |
|---|---|
| `is_subreddit_allowed` | Allowlist enforcement |
| `is_study_active` | Study must be marked `active: true` |
| `missing_required_fields` | Title, URL, IRB statement, eligibility must be present |
| `respects_subreddit_cooldown` | Per-subreddit minimum gap between posts |
| `respects_account_cooldown` | Per-account minimum gap between any two posts |
| `under_daily_post_limit` | Max posts per calendar day across all subreddits |
| `low_duplicate_risk` | No similar post to same subreddit within lookback window |

---

## Configuration

See [`examples/config.example.yaml`](examples/config.example.yaml) for the full schema.

Key settings:

```yaml
global_limits:
  daily_post_limit: 2
  per_account_min_gap_hours: 6

per_subreddit:
  cooldown_hours: 168    # 1 week between posts to the same subreddit

allowed_subreddits:
  - SampleSize
  - TakeMySurvey
```

---

## Post log

Every run appends rows to `post_log.csv` (gitignored). `examples/post_log_example.csv` shows the schema with fake data. Columns:

```
timestamp_iso, study_id, subreddit, action, reason, approver, reddit_post_id
```

`action` values: `skipped`, `declined_by_human`, `approved_disabled`, `posted` (last one only after API approval).

---

## Local dry-run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m reddit_scheduler --config examples/config.example.yaml --log examples/post_log_example.csv
```

The scheduler will run all gates and ask for human approval. If you approve, it will log `approved_disabled` and print:

```
Actual Reddit submission disabled until Reddit API approval.
```

No network calls to Reddit are made.

---

## Enabling posting (after API approval)

1. Create a `.env` file from `.env.example` and fill in real credentials.
2. In `src/reddit_scheduler/reddit_client.py`, set `POSTING_ENABLED = True` and implement the `praw.Reddit(...)` call in `submit_post()`.
3. Test with a single study against one subreddit before enabling the full scheduler.

---

## License

MIT — see [LICENSE](LICENSE).
