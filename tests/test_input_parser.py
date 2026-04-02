"""Tests for input parsing."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from depthreach.input_parser import load_prospects


def _write_tmp(content: str, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestLoadCSV:
    def test_minimal_csv(self):
        path = _write_tmp("name,email,company\nAlice,alice@example.com,Acme\n", ".csv")
        try:
            prospects = load_prospects(path)
        finally:
            os.unlink(path)
        assert len(prospects) == 1
        p = prospects[0]
        assert p.name == "Alice"
        assert p.email == "alice@example.com"
        assert p.company == "Acme"

    def test_multiple_rows(self):
        csv = "name,email\nAlice,a@x.com\nBob,b@x.com\n"
        path = _write_tmp(csv, ".csv")
        try:
            prospects = load_prospects(path)
        finally:
            os.unlink(path)
        assert [p.name for p in prospects] == ["Alice", "Bob"]

    def test_linkedin_alias(self):
        csv = "name,linkedin\nAlice,https://linkedin.com/in/alice\n"
        path = _write_tmp(csv, ".csv")
        try:
            prospects = load_prospects(path)
        finally:
            os.unlink(path)
        assert prospects[0].linkedin_url == "https://linkedin.com/in/alice"

    def test_extra_columns_preserved(self):
        csv = "name,email,phone\nAlice,a@x.com,555-1234\n"
        path = _write_tmp(csv, ".csv")
        try:
            prospects = load_prospects(path)
        finally:
            os.unlink(path)
        assert prospects[0].extra.get("phone") == "555-1234"

    def test_missing_name_raises(self):
        csv = "name,email\n,a@x.com\n"
        path = _write_tmp(csv, ".csv")
        try:
            with pytest.raises(ValueError, match="name"):
                load_prospects(path)
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_prospects("/tmp/nonexistent_depthreach_xyz.csv")

    def test_unsupported_extension(self):
        path = _write_tmp("name\nAlice\n", ".txt")
        try:
            with pytest.raises(ValueError, match="Unsupported"):
                load_prospects(path)
        finally:
            os.unlink(path)


class TestLoadJSON:
    def test_basic_json(self):
        data = [{"name": "Alice", "email": "a@x.com", "company": "Acme"}]
        path = _write_tmp(json.dumps(data), ".json")
        try:
            prospects = load_prospects(path)
        finally:
            os.unlink(path)
        assert len(prospects) == 1
        assert prospects[0].name == "Alice"

    def test_non_list_json_raises(self):
        path = _write_tmp('{"name": "Alice"}', ".json")
        try:
            with pytest.raises(ValueError, match="list"):
                load_prospects(path)
        finally:
            os.unlink(path)

    def test_missing_name_raises(self):
        data = [{"email": "a@x.com"}]
        path = _write_tmp(json.dumps(data), ".json")
        try:
            with pytest.raises(ValueError, match="name"):
                load_prospects(path)
        finally:
            os.unlink(path)
