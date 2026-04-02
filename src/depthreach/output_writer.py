"""CSV output writer with streaming support."""

from __future__ import annotations

import csv
import io
import sys
import threading
from typing import IO, Optional

from .models import EmailResult

_FIELDNAMES = ["name", "email", "company", "research_notes", "draft_email", "error"]


class OutputWriter:
    """Thread-safe, streaming CSV writer.

    Results are written incrementally as they arrive so the user can monitor
    progress with ``tail -f results.csv``.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        """
        Args:
            path: File path to write CSV to.  If None, output goes to stdout.
        """
        self._path = path
        self._lock = threading.Lock()
        self._header_written = False
        self._fh: Optional[IO[str]] = None
        self._writer: Optional[csv.DictWriter] = None

    def _ensure_open(self) -> None:
        if self._fh is None:
            if self._path:
                self._fh = open(self._path, "w", newline="", encoding="utf-8")
            else:
                self._fh = sys.stdout
            self._writer = csv.DictWriter(
                self._fh, fieldnames=_FIELDNAMES, extrasaction="ignore"
            )

    def write(self, result: EmailResult) -> None:
        """Write one result row.  Thread-safe."""
        with self._lock:
            self._ensure_open()
            if not self._header_written:
                self._writer.writeheader()  # type: ignore[union-attr]
                self._header_written = True
            self._writer.writerow(  # type: ignore[union-attr]
                {
                    "name": result.prospect.name,
                    "email": result.prospect.email,
                    "company": result.prospect.company,
                    "research_notes": result.research_notes,
                    "draft_email": result.draft_email,
                    "error": result.error or "",
                }
            )
            if self._fh and self._path:
                self._fh.flush()

    def close(self) -> None:
        with self._lock:
            if self._fh and self._path:
                self._fh.close()
                self._fh = None
