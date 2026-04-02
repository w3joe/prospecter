"""Local SQLite cache for research results."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Optional

_DEFAULT_DIR = os.path.expanduser("~/.depthreach")


def _get_cache_path(cache_dir: Optional[str] = None) -> str:
    directory = cache_dir or _DEFAULT_DIR
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "cache.sqlite")


class ResearchCache:
    """Persist and retrieve research results keyed by a prospect fingerprint."""

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self._db_path = _get_cache_path(cache_dir)
        self._conn = sqlite3.connect(self._db_path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_cache (
                key TEXT PRIMARY KEY,
                notes TEXT NOT NULL,
                raw_results TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def make_key(name: str, company: str) -> str:
        return f"{name.lower().strip()}|{company.lower().strip()}"

    def get(self, key: str) -> Optional[dict]:
        cursor = self._conn.execute(
            "SELECT notes, raw_results FROM research_cache WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"notes": row[0], "raw_results": json.loads(row[1])}

    def set(self, key: str, notes: str, raw_results: list) -> None:
        import time

        self._conn.execute(
            """
            INSERT OR REPLACE INTO research_cache (key, notes, raw_results, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, notes, json.dumps(raw_results), time.time()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
