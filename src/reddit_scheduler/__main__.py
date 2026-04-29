"""CLI entry point for the Reddit survey scheduler."""

from __future__ import annotations

import argparse

from . import config, scheduler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Human-approved survey post scheduler (Reddit API approval pending)."
    )
    parser.add_argument(
        "--config",
        default="examples/config.example.yaml",
        help="Path to scheduler config YAML (default: examples/config.example.yaml)",
    )
    parser.add_argument(
        "--log",
        default="post_log.csv",
        help="Path to the post log CSV file (default: post_log.csv)",
    )
    args = parser.parse_args()

    print(
        "\nReddit Survey Scheduler"
        "\nNOTE: Actual Reddit submission is DISABLED until Reddit Data API approval."
        "\n"
    )

    cfg = config.load(args.config)
    scheduler.run(cfg, args.log)

    print("\nScheduler run complete.")


if __name__ == "__main__":
    main()
