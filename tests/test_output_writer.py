"""Tests for the output writer."""

from __future__ import annotations

import csv
import io
import os
import tempfile

from depthreach.models import EmailResult, Prospect
from depthreach.output_writer import OutputWriter


def _make_result(name="Alice", email="a@x.com", company="Acme",
                 notes="notes", draft="draft", error="") -> EmailResult:
    return EmailResult(
        prospect=Prospect(name=name, email=email, company=company),
        research_notes=notes,
        draft_email=draft,
        error=error or None,
    )


class TestOutputWriter:
    def test_writes_to_file(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            writer = OutputWriter(path=path)
            writer.write(_make_result())
            writer.close()

            with open(path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 1
            assert rows[0]["name"] == "Alice"
            assert rows[0]["draft_email"] == "draft"
        finally:
            os.unlink(path)

    def test_writes_multiple_rows(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            writer = OutputWriter(path=path)
            writer.write(_make_result(name="Alice"))
            writer.write(_make_result(name="Bob"))
            writer.close()

            with open(path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            assert [r["name"] for r in rows] == ["Alice", "Bob"]
        finally:
            os.unlink(path)

    def test_error_field_written(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            writer = OutputWriter(path=path)
            writer.write(_make_result(error="API failed"))
            writer.close()

            with open(path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            assert rows[0]["error"] == "API failed"
        finally:
            os.unlink(path)
