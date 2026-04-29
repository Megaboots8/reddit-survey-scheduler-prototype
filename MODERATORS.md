# For Subreddit Moderators

If you moderate one of the subreddits this scheduler posts to and you would like the account `u/PerceptionStudies` to **stop posting** in your community, this page explains exactly how that works. We treat moderator opt-out requests as **mandatory** and **immediate**.

---

## How to opt out

1. Send a Reddit message to **`u/PerceptionStudies`**, open an issue on this repo, or email **anthony.walsh@mail.mcgill.ca**.
2. Include the name of your subreddit.
3. We will remove your subreddit from the `allowed_subreddits` list in our config within 24 hours and acknowledge by reply.

We **will not** continue posting to a subreddit after a moderator request to stop, regardless of the subreddit's stated rules.

---

## How the scheduler enforces opt-out

The list of subreddits we may post to is defined in `examples/config.example.yaml` under `allowed_subreddits`. The code in [`src/reddit_scheduler/safety_checks.py`](src/reddit_scheduler/safety_checks.py) refuses to post to any subreddit not on that list:

```python
def is_subreddit_allowed(subreddit: str, allowlist: list[str]) -> bool:
    return subreddit in allowlist
```

Removing your subreddit from the config is therefore both necessary and sufficient — there is no fallback path that would post to a non-allowlisted subreddit.

---

## What this scheduler does in your subreddit

When (and only when) Reddit Data API access is approved and your subreddit is on the allowlist:

- The account `u/PerceptionStudies` will submit a **self-text post** linking to a survey, on the schedule declared in our config (typically once per day in a given subreddit, with a 25-hour minimum gap between posts).
- Each post is **reviewed and approved by a human** before submission.
- Each post includes the subreddit's correct flair.
- Each post complies with the subreddit's posting rules — frequency, content, format. If your rules are stricter than our defaults, our config is updated to match yours.

## What this scheduler will never do in your subreddit

- It will not vote, upvote, or downvote any post or comment.
- It will not send DMs or chat messages to any user.
- It will not post automated comments or replies.
- It will not delete, edit, or lock posts after they go up.
- It will not scrape, store, or analyze user profiles, post histories, or any other Reddit user data.
- It will not interact with users beyond the survey post itself.
- It will not bypass any subreddit rule, ban, or rate limit.

---

## Data we collect from Reddit

**None.** This scheduler does not read any Reddit data — not user profiles, not comments on our own posts, not subscriber counts, not anything. Its only Reddit-side action is creating a post.

The only counts we track are aggregate response totals from our own surveys (e.g., "this Google Form has received 123 submissions"). That data lives entirely outside Reddit and is never tied to any Reddit account.

---

## Contact

- **Email:** anthony.walsh@mail.mcgill.ca
- **Reddit (developer):** `u/Fair_Imagination_410`
- **Reddit (posting account):** `u/PerceptionStudies`
- **GitHub Issues:** [this repo](https://github.com/Megaboots8/reddit-survey-scheduler-prototype/issues)

We aim to respond within 24 hours.
