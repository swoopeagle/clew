"""SQLite persistence for org profiles and grant prospects.

Single source of truth for the whole grant lifecycle: every prospect is one
row that moves through `STAGES`. The deadline tracker, submission board,
reporting reminders, and org-learning capture are all views or transitions
on this one table, not separate systems.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

_DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "clew.db")


def _db_path() -> str:
    return os.environ.get("CLEW_DB_PATH", _DEFAULT_DB_PATH)


# Ordered lifecycle stages. "passed" is a terminal branch off "qualified"
# (human said no at shortlist time); "declined" is a terminal branch off
# "submitted" (funder said no after a real application).
STAGES = [
    "qualified",
    "approved",
    "applied",
    "submitted",
    "awarded",
    "declined",
    "passed",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS org_profile (
    org_id TEXT PRIMARY KEY,
    mission TEXT,
    geography TEXT,
    program_areas TEXT,
    grant_size_min INTEGER,
    grant_size_max INTEGER,
    exclusions TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prospects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    source_ref TEXT,
    program_area TEXT,
    geography TEXT,
    grant_size TEXT,
    fit_rationale TEXT,
    fit_sources TEXT,
    warm_path_note TEXT,
    stage TEXT NOT NULL DEFAULT 'qualified',
    deadline_date TEXT,
    report_due_date TEXT,
    reported_at TEXT,
    retro_note TEXT,
    slack_channel_id TEXT,
    slack_message_ts TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_org_profile(org_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM org_profile WHERE org_id = ?", (org_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def upsert_org_profile(
    org_id: str,
    mission: str,
    geography: str,
    program_areas: str,
    grant_size_min: int | None,
    grant_size_max: int | None,
    exclusions: str | None,
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO org_profile
                (org_id, mission, geography, program_areas, grant_size_min, grant_size_max, exclusions, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id) DO UPDATE SET
                mission=excluded.mission,
                geography=excluded.geography,
                program_areas=excluded.program_areas,
                grant_size_min=excluded.grant_size_min,
                grant_size_max=excluded.grant_size_max,
                exclusions=excluded.exclusions,
                updated_at=excluded.updated_at
            """,
            (
                org_id,
                mission,
                geography,
                program_areas,
                grant_size_min,
                grant_size_max,
                exclusions,
                _now(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_prospect(
    org_id: str,
    name: str,
    source: str,
    source_ref: str | None,
    program_area: str | None,
    geography: str | None,
    grant_size: str | None,
    fit_rationale: str,
    fit_sources: list[str],
    warm_path_note: str | None = None,
) -> int:
    conn = _connect()
    try:
        now = _now()
        cur = conn.execute(
            """
            INSERT INTO prospects
                (org_id, name, source, source_ref, program_area, geography, grant_size,
                 fit_rationale, fit_sources, warm_path_note, stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'qualified', ?, ?)
            """,
            (
                org_id,
                name,
                source,
                source_ref,
                program_area,
                geography,
                grant_size,
                fit_rationale,
                json.dumps(fit_sources),
                warm_path_note,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_prospect(prospect_id: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_prospect(prospect_id: int, **fields) -> None:
    """Update arbitrary columns on a prospect row (e.g. stage, deadline_date,
    slack_message_ts, retro_note). Always bumps updated_at."""
    if not fields:
        return
    fields["updated_at"] = _now()
    columns = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [prospect_id]
    conn = _connect()
    try:
        conn.execute(f"UPDATE prospects SET {columns} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def get_prospects_grouped_by_stage(org_id: str) -> dict[str, list[dict]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM prospects WHERE org_id = ? ORDER BY updated_at DESC",
            (org_id,),
        ).fetchall()
        grouped: dict[str, list[dict]] = {stage: [] for stage in STAGES}
        for row in rows:
            grouped.setdefault(row["stage"], []).append(dict(row))
        return grouped
    finally:
        conn.close()
