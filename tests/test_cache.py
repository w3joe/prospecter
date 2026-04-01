"""Tests for the research cache."""

from __future__ import annotations

import tempfile
import os

from depthreach.cache import ResearchCache


def _tmp_cache() -> ResearchCache:
    tmpdir = tempfile.mkdtemp()
    return ResearchCache(cache_dir=tmpdir), tmpdir


class TestResearchCache:
    def test_miss_returns_none(self):
        cache, tmpdir = _tmp_cache()
        assert cache.get("nonexistent") is None
        cache.close()

    def test_set_and_get(self):
        cache, tmpdir = _tmp_cache()
        cache.set("alice|acme", "Some research notes", [{"title": "t"}])
        result = cache.get("alice|acme")
        assert result is not None
        assert result["notes"] == "Some research notes"
        assert result["raw_results"] == [{"title": "t"}]
        cache.close()

    def test_overwrite(self):
        cache, tmpdir = _tmp_cache()
        cache.set("key", "v1", [])
        cache.set("key", "v2", [])
        assert cache.get("key")["notes"] == "v2"
        cache.close()

    def test_make_key_normalisation(self):
        key = ResearchCache.make_key("  Alice  ", "  ACME  ")
        assert key == "alice|acme"
