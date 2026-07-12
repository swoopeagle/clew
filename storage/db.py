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
    grant_channel_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Columns added after the first release; applied to pre-existing DBs.
_MIGRATIONS = [
    "ALTER TABLE prospects ADD COLUMN grant_channel_id TEXT",
    "ALTER TABLE org_profile ADD COLUMN briefing_channel_id TEXT",
]


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
        for migration in _MIGRATIONS:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass  # column already exists
        conn.commit()
    finally:
        conn.close()


def list_org_ids() -> list[str]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT org_id FROM org_profile").fetchall()
        return [row["org_id"] for row in rows]
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


def find_prospect_by_identity(
    org_id: str, name: str, source_ref: str | None = None
) -> dict | None:
    """Find an existing prospect for this org that matches by source_ref (when
    given) or, failing that, by case-insensitive name. Used to avoid inserting
    duplicates when Find Grants is run more than once."""
    conn = _connect()
    try:
        if source_ref:
            row = conn.execute(
                "SELECT * FROM prospects WHERE org_id = ? AND source_ref = ?",
                (org_id, source_ref),
            ).fetchone()
            if row:
                return dict(row)
        row = conn.execute(
            "SELECT * FROM prospects WHERE org_id = ? AND lower(name) = lower(?)",
            (org_id, name),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_prospect_by_grant_channel(channel_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM prospects WHERE grant_channel_id = ?", (channel_id,)
        ).fetchone()
        return dict(row) if row else None
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


def claim_prospect_stage(prospect_id: int, from_stage: str, to_stage: str) -> bool:
    """Atomically move a prospect from one stage to another, but only if it is
    still in ``from_stage``. Returns True if this call made the transition,
    False if the row was already past ``from_stage`` (e.g. a double-clicked
    Approve button). The single UPDATE ... WHERE stage = ? is the atomic guard,
    so two near-simultaneous clicks can't both spin up a war room."""
    conn = _connect()
    try:
        cur = conn.execute(
            "UPDATE prospects SET stage = ?, updated_at = ? WHERE id = ? AND stage = ?",
            (to_stage, _now(), prospect_id, from_stage),
        )
        conn.commit()
        return cur.rowcount == 1
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


def set_briefing_channel(org_id: str, channel_id: str) -> None:
    """Where the daily briefing lands; set when someone asks for one."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE org_profile SET briefing_channel_id = ?, updated_at = ? "
            "WHERE org_id = ?",
            (channel_id, _now(), org_id),
        )
        conn.commit()
    finally:
        conn.close()


def list_briefing_targets() -> list[dict]:
    """(org_id, briefing_channel_id) pairs that opted into daily briefings."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT org_id, briefing_channel_id FROM org_profile "
            "WHERE briefing_channel_id IS NOT NULL"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def reset_org(org_id: str) -> dict:
    """Wipe an org for demo re-testing: delete its profile and every
    prospect. Returns what was removed so the caller can archive the
    war-room channels."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT grant_channel_id FROM prospects "
            "WHERE org_id = ? AND grant_channel_id IS NOT NULL",
            (org_id,),
        ).fetchall()
        channel_ids = [row["grant_channel_id"] for row in rows]
        cur = conn.execute("DELETE FROM prospects WHERE org_id = ?", (org_id,))
        prospect_count = cur.rowcount
        conn.execute("DELETE FROM org_profile WHERE org_id = ?", (org_id,))
        conn.commit()
        return {"grant_channel_ids": channel_ids, "prospect_count": prospect_count}
    finally:
        conn.close()
