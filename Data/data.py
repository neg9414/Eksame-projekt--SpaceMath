"""Data lag for SpaceMath.
Denne fil står for alt der har med dataen at gøre, jeg bruger den til at gemme elever og deres scores i en database. Det er en simpel SQLite database
"""

from __future__ import annotations

#jeg bruger sqlite3, fordi det er en simpel database og er nem at arbejde med samt det er det vi har lært
import sqlite3
from pathlib import Path
from typing import Any, Dict

#definer hvor database ligger
DB_PATH = Path(__file__).resolve().parent / "spacemath.db"

#denne klasse står for at kommunikation med databasen
class Database:

#her gemmer jeg stilen til databasen, så den er nem at ændre hvis jeg vil bruge en anden database senere
    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

#opretter forbindelse til databasen
    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self.path))

#row_factory gør at jeg kan få resultaterne som dicts i stedet for tuples, så det er nemmere at arbejde med
        self._conn.row_factory = sqlite3.Row

#søger for at tabllerne er oprettet i databasen
        self._ensure_schema()

#her opretter jeg tabellerne hvis de ikke findes
    def _ensure_schema(self) -> None:
        assert self._conn is not None
        cur = self._conn.cursor()

#jeg bruger IF NOT EXISTS så programmet ikke crasher hvis tabellerne allerede findes, og jeg definerer tabellerne med de nødvendige felter til at gemme elever og deres scores
        cur.execute(
            """CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS games ( id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, score INTEGER NOT NULL, problems_solved INTEGER NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(student_id) REFERENCES students(id))"""
        )
        self._conn.commit()

    def add_student(self, name: str) -> int:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
        self._conn.commit()
        cur.execute("SELECT id FROM students WHERE name = ?", (name,))
        row = cur.fetchone()
        return int(row["id"])

    def save_game(self, student_id: int, score: int, problems_solved: int) -> None:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO games (student_id, score, problems_solved) VALUES (?, ?, ?)",
            (student_id, score, problems_solved),
        )
        self._conn.commit()

    def get_last_game_score(self, student_id: int) -> int:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "SELECT score FROM games WHERE student_id = ? ORDER BY timestamp DESC LIMIT 1",
            (student_id,),
        )
        row = cur.fetchone()
        return int(row["score"]) if row else 0

#her henter jeg statistik for en elev, hvor jeg tæller hvor mange spil de har spillet, hvad deres totale score er og hvad deres gennemsnitlige score er
    def get_stats(self, student_id: int) -> Dict[str, Any]:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS games_played, SUM(score) AS total_score, AVG(score) AS avg_score FROM games WHERE student_id = ?",
            (student_id,),
        )
        row = cur.fetchone()
        return {
            "games_played": int(row["games_played"] or 0),
            "total_score": int(row["total_score"] or 0),
            "avg_score": float(row["avg_score"] or 0.0),
        }

#her henter jeg alle spil for en elev, som bruges til at vise en liste af tidligere scores i UI
    def get_all_games(self, student_id: int) -> list[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, student_id, score, problems_solved, timestamp FROM games WHERE student_id = ? ORDER BY timestamp DESC",
            (student_id,),
        )
        return cur.fetchall()

#jeg bruger JOIN til at kombinere data fra flere tabeller til læreroversigten
    def get_all_students(self) -> list[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT
                s.id,
                s.name,
                COUNT(g.id) AS games_played,
                COALESCE(SUM(g.score), 0) AS total_score
            FROM students s
            LEFT JOIN games g ON s.id = g.student_id
            GROUP BY s.id, s.name
            ORDER BY s.name
            """,
        )
        return cur.fetchall()

#lukker så forbindelsen til databasen så der undgå fejl og memory leaks
    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
