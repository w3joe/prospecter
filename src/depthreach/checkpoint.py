"""Checkpoint support for resumable batch processing."""

from __future__ import annotations

import json
import os
from typing import Optional, Set

_DEFAULT_DIR = os.path.expanduser("~/.depthreach")


def _get_state_path(state_dir: Optional[str] = None) -> str:
    directory = state_dir or _DEFAULT_DIR
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "state.json")


class Checkpoint:
    """Track which prospects have been fully processed so jobs can be resumed."""

    def __init__(self, state_dir: Optional[str] = None) -> None:
        self._path = _get_state_path(state_dir)
        self._completed: Set[str] = set()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as fh:
                    data = json.load(fh)
                self._completed = set(data.get("completed", []))
            except (json.JSONDecodeError, OSError):
                self._completed = set()

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump({"completed": sorted(self._completed)}, fh, indent=2)

    @staticmethod
    def make_key(name: str, email: str) -> str:
        return f"{name.lower().strip()}|{email.lower().strip()}"

    def is_done(self, key: str) -> bool:
        return key in self._completed

    def mark_done(self, key: str) -> None:
        self._completed.add(key)
        self._save()

    def clear(self) -> None:
        self._completed.clear()
        if os.path.exists(self._path):
            os.remove(self._path)
