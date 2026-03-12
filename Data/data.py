"""Data layer for SpaceMath.

This module handles saving and loading persistent data (scores, progress, and students).
It is intentionally independent of Pygame and any UI code.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict

DB_PATH = Path(__file__).resolve().parent / "spacemath.db"


class Database:
    """Simple SQLite-backed database for storing student scores."""

    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open the database connection and ensure tables exist."""
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
            """
        )
        self._conn.commit()

    def add_student(self, name: str) -> int:
        """Create a student record (or find existing) and return the student id."""
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
        self._conn.commit()
        cur.execute("SELECT id FROM students WHERE name = ?", (name,))
        row = cur.fetchone()
        return int(row["id"])

    def save_score(self, student_id: int, score: int) -> None:
        """Save a new score for a student."""
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO scores (student_id, score) VALUES (?, ?)",
            (student_id, score),
        )
        self._conn.commit()

    def get_latest_score(self, student_id: int) -> int:
        """Return the most recent score for a student (or 0 if none)."""
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "SELECT score FROM scores WHERE student_id = ? ORDER BY timestamp DESC LIMIT 1",
            (student_id,),
        )
        row = cur.fetchone()
        return int(row["score"]) if row else 0

    def get_stats(self, student_id: int) -> Dict[str, Any]:
        """Return simple statistics for a student (attempts, average score)."""
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS attempts, AVG(score) AS avg_score FROM scores WHERE student_id = ?",
            (student_id,),
        )
        row = cur.fetchone()
        return {
            "attempts": int(row["attempts"] or 0),
            "avg_score": float(row["avg_score"] or 0.0),
        }

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
