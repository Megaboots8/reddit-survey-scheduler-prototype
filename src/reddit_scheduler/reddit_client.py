"""
Reddit API client stub.

Actual Reddit submission is disabled until Reddit Data API access is approved.
The full scheduler flow (allowlist, cooldowns, daily limits, human approval)
runs end-to-end so the logic can be reviewed and tested. Only the final
network call to Reddit is gated here.

To enable posting after API approval:
  1. Set POSTING_ENABLED = True.
  2. Fill in credentials in .env (copy from .env.example).
  3. Implement the praw.Reddit(...) call in submit_post() below.
"""

POSTING_ENABLED = False  # Flip to True after Reddit Data API approval.


class PostingDisabledError(RuntimeError):
    """Raised when submit_post() is called while POSTING_ENABLED is False."""


def submit_post(subreddit: str, title: str, body: str) -> str:
    """Submit a self-text post to the given subreddit.

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
    # submission = reddit.subreddit(subreddit).submit(title=title, selftext=body)
    # return submission.id

    raise NotImplementedError("submit_post() not yet implemented.")
