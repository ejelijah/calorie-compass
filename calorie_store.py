"""SQLite persistence and calorie calculations for Neo_Cal."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

EntryType = Literal["in", "out"]
DEFAULT_DB_PATH = Path(__file__).parent / "data" / "calorie_log.db"


def _connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS calorie_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                entry_type TEXT NOT NULL CHECK (entry_type IN ('in', 'out')),
                description TEXT NOT NULL,
                calories INTEGER NOT NULL CHECK (calories > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_calorie_entries_date
            ON calorie_entries (entry_date, id)
            """
        )


def add_entry(
    entry_date: date,
    entry_type: EntryType,
    description: str,
    calories: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Save an intake or expenditure entry and return its database ID."""
    clean_description = description.strip()
    if entry_type not in ("in", "out"):
        raise ValueError("Entry type must be 'in' or 'out'.")
    if not clean_description:
        raise ValueError("Description must not be blank.")
    if isinstance(calories, bool) or not isinstance(calories, int) or calories <= 0:
        raise ValueError("Calories must be a positive whole number.")

    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO calorie_entries (entry_date, entry_type, description, calories)
            VALUES (?, ?, ?, ?)
            """,
            (entry_date.isoformat(), entry_type, clean_description, calories),
        )
        return int(cursor.lastrowid)


def get_entries(
    entry_date: date, db_path: str | Path = DEFAULT_DB_PATH
) -> list[dict[str, object]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, entry_date, entry_type, description, calories, created_at
            FROM calorie_entries
            WHERE entry_date = ?
            ORDER BY id DESC
            """,
            (entry_date.isoformat(),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_daily_totals(
    entry_date: date, db_path: str | Path = DEFAULT_DB_PATH
) -> dict[str, int]:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN entry_type = 'in' THEN calories ELSE 0 END), 0) AS calories_in,
                COALESCE(SUM(CASE WHEN entry_type = 'out' THEN calories ELSE 0 END), 0) AS calories_out
            FROM calorie_entries
            WHERE entry_date = ?
            """,
            (entry_date.isoformat(),),
        ).fetchone()

    calories_in = int(row["calories_in"])
    calories_out = int(row["calories_out"])
    return {
        "calories_in": calories_in,
        "calories_out": calories_out,
        "net": calories_in - calories_out,
    }


def get_daily_history(
    end_date: date, days: int = 7, db_path: str | Path = DEFAULT_DB_PATH
) -> list[dict[str, object]]:
    if days < 1:
        raise ValueError("Days must be at least one.")
    start_date = end_date - timedelta(days=days - 1)

    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                entry_date,
                SUM(CASE WHEN entry_type = 'in' THEN calories ELSE 0 END) AS calories_in,
                SUM(CASE WHEN entry_type = 'out' THEN calories ELSE 0 END) AS calories_out
            FROM calorie_entries
            WHERE entry_date BETWEEN ? AND ?
            GROUP BY entry_date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

    totals_by_date = {
        str(row["entry_date"]): (
            int(row["calories_in"]),
            int(row["calories_out"]),
        )
        for row in rows
    }
    history = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        calories_in, calories_out = totals_by_date.get(day.isoformat(), (0, 0))
        history.append(
            {
                "date": day.isoformat(),
                "calories_in": calories_in,
                "calories_out": calories_out,
                "net": calories_in - calories_out,
            }
        )
    return history


def delete_entry(entry_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> bool:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM calorie_entries WHERE id = ?", (entry_id,)
        )
        return cursor.rowcount == 1


def get_database_path() -> Path:
    configured_path = os.environ.get("NEO_CAL_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DB_PATH
