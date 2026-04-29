"""
Study status integrations.

Reads the *aggregate* response counts for a study from its declared data
source (Google Sheets or a MySQL database). The scheduler uses this to:

  1. Verify a study's data source is reachable before posting.
  2. Annotate each post log row with the response/completion counts at
     post time, for tracking effectiveness over time.

DATA HANDLING POLICY
====================
This module reads only **aggregate counts** — the number of rows in a
sheet, or COUNT(*) from a database table. It never:

  - reads, returns, or transmits any individual respondent's answers,
  - reads, returns, or transmits any personally identifiable information,
  - reads, returns, or transmits any Reddit user data (this module
    does not interact with Reddit at all).

External integrations are gated behind SHEETS_ENABLED and MYSQL_ENABLED
flags. While disabled, this module returns deterministic mock counts so
the rest of the scheduler can run end-to-end for review without any
network access or credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

SHEETS_ENABLED = False  # Flip to True after Google Sheets credentials are configured.
MYSQL_ENABLED = False   # Flip to True after MySQL credentials are configured.


class IntegrationDisabledError(RuntimeError):
    """Raised when a real-network call is attempted while the integration is disabled."""


@dataclass
class StudyStatus:
    response_count: int
    completion_count: int
    last_checked_iso: str
    source: str  # e.g. "sheets:mock", "mysql:mock", "sheets", "mysql"


def get_status(study: dict) -> StudyStatus:
    """Return aggregate status for a study from its declared data source.

    Aggregate counts only — never individual respondent data. See module
    docstring for the data handling policy.
    """
    data_source = study.get("data_source", {}) or {}
    source_type = data_source.get("type", "none")

    if source_type == "sheets":
        return _from_sheets(data_source)
    if source_type == "mysql":
        return _from_mysql(data_source)
    return StudyStatus(0, 0, _now_iso(), "none")


def _from_sheets(data_source: dict) -> StudyStatus:
    """Read aggregate response count from a Google Sheets form-responses tab.

    Production implementation reads only the first column (timestamp column
    of a Google Form's responses sheet) and returns its length minus the
    header row. No individual response cells are read.
    """
    if not SHEETS_ENABLED:
        return StudyStatus(
            response_count=123,
            completion_count=87,
            last_checked_iso=_now_iso(),
            source="sheets:mock",
        )

    # Production implementation (uncomment after credentials are configured):
    #
    # from googleapiclient.discovery import build
    # from google.oauth2.credentials import Credentials
    #
    # creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/spreadsheets.readonly"])
    # service = build("sheets", "v4", credentials=creds)
    # result = service.spreadsheets().values().get(
    #     spreadsheetId=data_source["sheet_id"],
    #     range=data_source["range"],
    # ).execute()
    # values = result.get("values", [])
    # response_count = max(len(values) - 1, 0)   # subtract header row
    # completion_count = response_count          # forms-only: every row is a submission
    # return StudyStatus(response_count, completion_count, _now_iso(), "sheets")

    raise IntegrationDisabledError(
        "Google Sheets integration disabled. Set SHEETS_ENABLED=True after credentials are configured."
    )


def _from_mysql(data_source: dict) -> StudyStatus:
    """Read aggregate counts from a MySQL experiment table over an SSH tunnel.

    Production implementation issues two SELECT COUNT(*) queries:
      1. Total rows in the table.
      2. Rows where the configured complete_filter is true.

    Read-only. The configured DB user has SELECT-only privileges. No
    individual rows are ever fetched, only counts.
    """
    if not MYSQL_ENABLED:
        return StudyStatus(
            response_count=410,
            completion_count=117,
            last_checked_iso=_now_iso(),
            source="mysql:mock",
        )

    # Production implementation (uncomment after credentials are configured):
    #
    # import os
    # import pymysql
    # from sshtunnel import SSHTunnelForwarder
    #
    # with SSHTunnelForwarder(
    #     (os.environ["SSH_HOST"], int(os.environ["SSH_PORT"])),
    #     ssh_username=os.environ["SSH_USER"],
    #     ssh_password=os.environ["SSH_PASSWORD"],
    #     remote_bind_address=(os.environ["MYSQL_HOST"], int(os.environ["MYSQL_PORT"])),
    # ) as tunnel:
    #     conn = pymysql.connect(
    #         host="127.0.0.1",
    #         port=tunnel.local_bind_port,
    #         user=os.environ["MYSQL_USER"],
    #         password=os.environ["MYSQL_PASSWORD"],
    #         database=data_source["database"],
    #         connect_timeout=10,
    #     )
    #     try:
    #         with conn.cursor() as cur:
    #             cur.execute(f"SELECT COUNT(*) FROM `{data_source['table']}`")
    #             total = cur.fetchone()[0]
    #             cur.execute(
    #                 f"SELECT COUNT(*) FROM `{data_source['table']}` "
    #                 f"WHERE {data_source['complete_filter']}"
    #             )
    #             complete = cur.fetchone()[0]
    #     finally:
    #         conn.close()
    # return StudyStatus(total, complete, _now_iso(), "mysql")

    raise IntegrationDisabledError(
        "MySQL integration disabled. Set MYSQL_ENABLED=True after credentials are configured."
    )


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
