"""
Reddit API client stub.

Actual Reddit submission is disabled until Reddit Data API access is approved.
The full scheduler flow (allowlist, schedule, study status, cooldowns,
daily limits, human approval) runs end-to-end so the logic can be reviewed
and tested. Only the final network call to Reddit is gated here.

To enable posting after API approval:
  1. Set POSTING_ENABLED = True.
  2. Fill in credentials in .env (copy from .env.example).
  3. Implement the praw.Reddit(...) call in submit_post() below.
"""

POSTING_ENABLED = False  # Flip to True after Reddit Data API approval.


class PostingDisabledError(RuntimeError):
    """Raised when submit_post() is called while POSTING_ENABLED is False."""


def submit_post(subreddit: str, title: str, body: str, flair: str = "") -> str:
    """Submit a self-text post to the given subreddit with optional flair.

    Returns the Reddit post ID string on success.

    Actual Reddit submission disabled until Reddit API approval.
    """
    if not POSTING_ENABLED:
        raise PostingDisabledError(
            "Actual Reddit submission disabled until Reddit API approval."
        )

    # Production implementation (uncomment after API approval):
    #
    # import os
    # import praw
    # reddit = praw.Reddit(
    #     client_id=os.environ["REDDIT_CLIENT_ID"],
    #     client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    #     username=os.environ["REDDIT_USERNAME"],
    #     password=os.environ["REDDIT_PASSWORD"],
    #     user_agent=os.environ["REDDIT_USER_AGENT"],
    # )
    # sub = reddit.subreddit(subreddit)
    # flair_template_id = _resolve_flair_template_id(sub, flair) if flair else None
    # submission = sub.submit(
    #     title=title,
    #     selftext=body,
    #     flair_id=flair_template_id,
    #     send_replies=False,  # Comment notifications routed via Reddit, not DMs.
    # )
    # return submission.id

    raise NotImplementedError("submit_post() not yet implemented.")


def _resolve_flair_template_id(subreddit, flair_label: str):
    """Look up the flair_template_id for a given human-readable flair label.

    Subreddits define flair templates with internal UUIDs; praw needs the
    UUID, not the visible label. This helper looks up the matching template
    via subreddit.flair.link_templates and returns its id, or None if no
    matching template exists (in which case we post without flair).
    """
    # Production implementation:
    # for template in subreddit.flair.link_templates:
    #     if template["text"].strip().lower() == flair_label.strip().lower():
    #         return template["id"]
    # return None
    raise NotImplementedError
