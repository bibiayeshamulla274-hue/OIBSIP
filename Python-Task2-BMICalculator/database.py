"""
database.py
SQLite persistence layer for the BMI Calculator (Advanced Tier).
Manages user BMI records in 'bmi_data.db' with safe error handling.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional


class DatabaseError(Exception):
    """Custom exception raised when a SQLite database operation fails."""
    pass


# Store bmi_data.db in the same directory as this script
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmi_data.db")


class BMIDatabase:
    """Encapsulates all SQLite read/write operations for BMI records."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def initialize_db(self) -> None:
        """Create the bmi_records table if it does not already exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        date_time TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_meta (
                        meta_key TEXT PRIMARY KEY,
                        meta_value TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to initialize database: {exc}") from exc

    def count_records(self) -> int:
        """Return total number of saved BMI records across all users."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM bmi_records")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to count BMI records: {exc}") from exc

    def seed_sample_data(self, force: bool = False) -> int:
        """
        Populate realistic multi-user dummy records on first run (or when forced).
        Returns the number of inserted sample rows.
        """
        sample_rows = [
            ("Ayesha", 73.5, 1.66, 26.67, "Overweight", "2026-09-02 09:15:00"),
            ("Ayesha", 71.2, 1.66, 25.84, "Overweight", "2026-09-18 09:20:00"),
            ("Ayesha", 68.4, 1.66, 24.82, "Normal", "2026-10-05 08:50:00"),
            ("Ayesha", 65.8, 1.66, 23.88, "Normal", "2026-10-22 09:05:00"),
            ("Ayesha", 63.2, 1.66, 22.93, "Normal", "2026-11-10 09:10:00"),
            ("Rahul", 51.0, 1.72, 17.24, "Underweight", "2026-09-10 18:30:00"),
            ("Rahul", 53.5, 1.72, 18.08, "Underweight", "2026-10-01 18:45:00"),
            ("Rahul", 56.4, 1.72, 19.06, "Normal", "2026-10-20 19:00:00"),
            ("Rahul", 58.8, 1.72, 19.88, "Normal", "2026-11-08 18:40:00"),
            ("Priya", 88.0, 1.64, 32.72, "Obese", "2026-09-14 07:30:00"),
            ("Priya", 84.5, 1.64, 31.42, "Obese", "2026-10-04 07:45:00"),
            ("Priya", 79.8, 1.64, 29.67, "Overweight", "2026-10-28 07:40:00"),
            ("Priya", 76.5, 1.64, 28.44, "Overweight", "2026-11-12 07:50:00"),
        ]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if not force:
                    cursor.execute("SELECT meta_value FROM app_meta WHERE meta_key = 'sample_seeded'")
                    if cursor.fetchone() is not None:
                        return 0
                    cursor.execute("SELECT COUNT(*) FROM bmi_records")
                    existing = cursor.fetchone()[0]
                    if existing > 0:
                        cursor.execute(
                            "INSERT OR REPLACE INTO app_meta (meta_key, meta_value) VALUES ('sample_seeded', '1')"
                        )
                        conn.commit()
                        return 0

                cursor.executemany(
                    """
                    INSERT INTO bmi_records (username, weight, height, bmi, category, date_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    sample_rows,
                )
                cursor.execute(
                    "INSERT OR REPLACE INTO app_meta (meta_key, meta_value) VALUES ('sample_seeded', '1')"
                )
                conn.commit()
                return len(sample_rows)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to seed sample data: {exc}") from exc

    def insert_record(
        self,
        username: str,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        date_time: Optional[str] = None,
    ) -> int:
        """
        Insert a new BMI calculation record for the given username.
        Returns the newly created record ID.
        """
        timestamp = date_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_name = username.strip()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO bmi_records (username, weight, height, bmi, category, date_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (clean_name, weight, height, bmi, category, timestamp),
                )
                conn.commit()
                return int(cursor.lastrowid)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save BMI record: {exc}") from exc

    def get_user_records(self, username: str) -> List[Tuple[int, str, float, float, float, str, str]]:
        """
        Retrieve all BMI records for a given username ordered chronologically.
        Matches usernames case-insensitively while preserving stored casing.
        """
        clean_name = username.strip()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, username, weight, height, bmi, category, date_time
                    FROM bmi_records
                    WHERE LOWER(username) = LOWER(?)
                    ORDER BY id ASC
                    """,
                    (clean_name,),
                )
                return cursor.fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to load history for '{clean_name}': {exc}") from exc

    def get_all_usernames(self) -> List[str]:
        """Return a sorted list of distinct usernames stored in the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT DISTINCT username
                    FROM bmi_records
                    ORDER BY LOWER(username) ASC
                    """
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to load user list: {exc}") from exc

    def delete_user_records(self, username: str) -> int:
        """
        Delete all BMI records belonging to the specified username.
        Returns the number of deleted rows.
        """
        clean_name = username.strip()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM bmi_records
                    WHERE LOWER(username) = LOWER(?)
                    """,
                    (clean_name,),
                )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to delete records for '{clean_name}': {exc}") from exc
