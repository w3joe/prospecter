"""Tests for the CLI argument parser and integration."""

from __future__ import annotations

import pytest

from depthreach.cli import build_parser


class TestBuildParser:
    def test_batch_mode_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["--input", "prospects.csv"])
        assert args.input == "prospects.csv"
        assert args.output is None
        assert args.workers == 2
        assert args.tone == "professional"
        assert not args.verbose

    def test_batch_mode_all_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            "--input", "p.csv",
            "--output", "out.csv",
            "--tone", "casual",
            "--workers", "3",
            "--verbose",
        ])
        assert args.output == "out.csv"
        assert args.tone == "casual"
        assert args.workers == 3
        assert args.verbose

    def test_single_mode(self):
        parser = build_parser()
        args = parser.parse_args(["--name", "Alice", "--company", "Acme", "--email", "a@acme.com"])
        assert args.name == "Alice"
        assert args.company == "Acme"
        assert args.email == "a@acme.com"

    def test_invalid_tone_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--input", "p.csv", "--tone", "aggressive"])

    def test_invalid_workers_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--input", "p.csv", "--workers", "5"])
