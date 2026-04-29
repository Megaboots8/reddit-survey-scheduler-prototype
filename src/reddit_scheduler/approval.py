"""Human approval prompt shown before any post attempt."""

from __future__ import annotations


def confirm_post(preview: str) -> tuple[bool, str]:
    """Print the post preview and ask the operator to approve or decline.

    Returns (approved: bool, approver_name: str).
    The approver name is recorded in the post log for audit purposes.
    The operator must type the literal string 'YES' (case-sensitive) to
    approve. Anything else — including 'y', 'yes', whitespace, or
    pressing Enter — declines. This is intentionally stricter than
    typical y/N prompts so approval cannot happen by accident.
    """
    print("\n" + "=" * 60)
    print("PENDING HUMAN APPROVAL")
    print("=" * 60)
    print(preview)
    print("=" * 60)

    answer = input("Approve this post? Type YES to submit: ").strip()
    if answer != "YES":
        return False, ""

    approver = input("Enter your name/handle for the log: ").strip()
    return True, approver
