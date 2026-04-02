"""Tests for the researcher module (using mocked Tavily)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from depthreach.models import Prospect
from depthreach.researcher import RateLimiter, _summarise_results, research_prospect


class TestSummariseResults:
    def test_empty_results(self):
        p = Prospect(name="Alice", company="Acme")
        notes = _summarise_results([], p)
        assert "No public information" in notes

    def test_formats_results(self):
        p = Prospect(name="Alice", company="Acme")
        results = [
            {"title": "Alice joins Acme", "content": "Alice has joined Acme.", "url": "https://example.com"}
        ]
        notes = _summarise_results(results, p)
        assert "Alice joins Acme" in notes
        assert "https://example.com" in notes


class TestResearchProspect:
    def test_returns_error_on_missing_tavily(self):
        """If tavily is not importable, return an error result."""
        p = Prospect(name="Alice", company="Acme")
        rl = RateLimiter(max_requests=10, window_seconds=60)
        with patch.dict("sys.modules", {"tavily": None}):
            result = research_prospect(p, api_key="fake", rate_limiter=rl)
        assert result.error is not None
        assert "tavily" in result.error.lower()

    def test_successful_research(self):
        p = Prospect(name="Alice", company="Acme")
        rl = RateLimiter(max_requests=10, window_seconds=60)

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "answer": "Alice is a CEO at Acme.",
            "results": [
                {"title": "Alice CEO", "content": "She leads the team.", "url": "https://ex.com"}
            ],
        }

        mock_tavily = MagicMock()
        mock_tavily.TavilyClient.return_value = mock_client

        with patch.dict("sys.modules", {"tavily": mock_tavily}):
            result = research_prospect(p, api_key="fake", rate_limiter=rl)

        assert result.error is None
        assert "Alice is a CEO" in result.notes or "Alice CEO" in result.notes

    def test_api_exception_returns_error(self):
        p = Prospect(name="Alice", company="Acme")
        rl = RateLimiter(max_requests=10, window_seconds=60)

        mock_client = MagicMock()
        mock_client.search.side_effect = RuntimeError("API down")

        mock_tavily = MagicMock()
        mock_tavily.TavilyClient.return_value = mock_client

        with patch.dict("sys.modules", {"tavily": mock_tavily}):
            result = research_prospect(p, api_key="fake", rate_limiter=rl)

        assert result.error is not None
        assert "API down" in result.error
