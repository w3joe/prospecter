"""Input parsing: CSV and JSON prospect lists."""

from __future__ import annotations

import csv
import json
import os
from typing import List

from .models import Prospect

_KNOWN_FIELDS = {"name", "email", "company", "linkedin_url", "linkedin"}


def load_prospects(path: str) -> List[Prospect]:
    """Load prospects from a CSV or JSON file.

    Required field: ``name``.
    Optional fields: ``email``, ``company``, ``linkedin_url`` (alias ``linkedin``).
    Any extra columns are kept in ``Prospect.extra``.

    Raises:
        ValueError: if the file extension is unsupported or required fields are missing.
        FileNotFoundError: if the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return _load_csv(path)
    elif ext == ".json":
        return _load_json(path)
    else:
        raise ValueError(f"Unsupported file format: {ext!r}. Use .csv or .json")


def _row_to_prospect(row: dict) -> Prospect:
    """Convert a dict row to a Prospect, normalising field names."""
    row = {k.strip().lower(): str(v).strip() for k, v in row.items() if k}
    name = row.get("name", "").strip()
    if not name:
        raise ValueError(f"Missing required field 'name' in row: {row}")
    # linkedin_url may also appear as "linkedin"
    linkedin_url = row.get("linkedin_url") or row.get("linkedin") or ""
    extra = {
        k: v for k, v in row.items() if k not in _KNOWN_FIELDS and k != "linkedin"
    }
    return Prospect(
        name=name,
        email=row.get("email", ""),
        company=row.get("company", ""),
        linkedin_url=linkedin_url,
        extra=extra,
    )


def _load_csv(path: str) -> List[Prospect]:
    prospects: List[Prospect] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty or has no header row")
        for i, row in enumerate(reader, start=2):  # row 1 is the header
            try:
                prospects.append(_row_to_prospect(row))
            except ValueError as exc:
                raise ValueError(f"Row {i}: {exc}") from exc
    return prospects


def _load_json(path: str) -> List[Prospect]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a top-level list of prospect objects")
    prospects: List[Prospect] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"JSON item {i} is not an object: {item!r}")
        try:
            prospects.append(_row_to_prospect(item))
        except ValueError as exc:
            raise ValueError(f"JSON item {i}: {exc}") from exc
    return prospects
