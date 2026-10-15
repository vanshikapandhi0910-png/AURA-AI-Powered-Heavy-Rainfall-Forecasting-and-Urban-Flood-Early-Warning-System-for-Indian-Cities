"""Persistent, explicitly unverified community experience reports."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

ROOT = Path(__file__).resolve().parents[1]
if os.environ.get("VERCEL"):
    DATABASE = Path("/tmp") / "aura-community-reports.sqlite3"
else:
    DATABASE = ROOT / "data" / "community_reports.sqlite3"


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS community_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_label TEXT NOT NULL,
                city TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                experience TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                created_at TEXT NOT NULL
            )
            """
        )
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def add_experience(report: dict) -> dict:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO community_experiences
                (location_label, city, state, category, experience, latitude, longitude, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report["location_label"],
                report.get("city", ""),
                report.get("state", ""),
                report["category"],
                report["experience"],
                report.get("latitude"),
                report.get("longitude"),
                created_at,
            ),
        )
        saved = connection.execute(
            "SELECT * FROM community_experiences WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _serialize(saved)


def get_experiences(limit: int = 100) -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM community_experiences ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_serialize(row) for row in rows]


def _serialize(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "location_label": row["location_label"],
        "city": row["city"],
        "state": row["state"],
        "category": row["category"],
        "experience": row["experience"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "created_at": row["created_at"],
        "data_status": "COMMUNITY SUBMITTED · UNVERIFIED",
    }
