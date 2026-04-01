"""Tests for the checkpoint module."""

from __future__ import annotations

import tempfile

from depthreach.checkpoint import Checkpoint


def _tmp_checkpoint() -> Checkpoint:
    tmpdir = tempfile.mkdtemp()
    return Checkpoint(state_dir=tmpdir)


class TestCheckpoint:
    def test_not_done_initially(self):
        cp = _tmp_checkpoint()
        assert not cp.is_done("alice|a@x.com")

    def test_mark_done(self):
        cp = _tmp_checkpoint()
        cp.mark_done("alice|a@x.com")
        assert cp.is_done("alice|a@x.com")

    def test_persists_across_instances(self):
        tmpdir = tempfile.mkdtemp()
        cp1 = Checkpoint(state_dir=tmpdir)
        cp1.mark_done("alice|a@x.com")

        cp2 = Checkpoint(state_dir=tmpdir)
        assert cp2.is_done("alice|a@x.com")

    def test_clear(self):
        cp = _tmp_checkpoint()
        cp.mark_done("alice|a@x.com")
        cp.clear()
        assert not cp.is_done("alice|a@x.com")

    def test_make_key_normalisation(self):
        key = Checkpoint.make_key("  Alice  ", "  A@X.COM  ")
        assert key == "alice|a@x.com"
