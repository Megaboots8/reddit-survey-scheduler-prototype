"""Human approval prompt shown before any post attempt."""

from __future__ import annotations


def confirm_post(preview: str) -> tuple[bool, str]:
    """Print the post preview and ask the operator to approve or decline.

    Returns (approved: bool, approver_name: str).
    The approver name is recorded in the post log for audit purposes.
    Typing anything other than 'y' or 'yes' (case-insensitive) declines.
    """
    print("\n" + "=" * 60)
    print("PENDING HUMAN APPROVAL")
    print("=" * 60)
    print(preview)
    print("=" * 60)

    answer = input("Approve this post? (y/N): ").strip()
    if answer.lower() not in ("y", "yes"):
        return False, ""

    approver = input("Enter your name/handle for the log: ").strip()
    return True, approver
