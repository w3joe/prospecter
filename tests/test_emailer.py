"""Tests for the email generator (using mocked Gemini)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from depthreach.emailer import generate_email
from depthreach.models import Prospect


class TestGenerateEmail:
    def test_returns_error_on_missing_genai(self):
        p = Prospect(name="Alice", company="Acme", email="alice@acme.com")
        with patch.dict("sys.modules", {"google.generativeai": None, "google": MagicMock()}):
            result = generate_email(p, research_notes="notes", api_key="fake")
        assert result.error is not None

    def test_successful_generation(self):
        p = Prospect(name="Alice", company="Acme", email="alice@acme.com")

        mock_response = MagicMock()
        mock_response.text = "Hi Alice, I loved reading about Acme's new product..."

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            result = generate_email(
                p,
                research_notes="Acme launched a new product.",
                api_key="fake",
                tone="professional",
            )

        assert result.error is None
        assert "Alice" in result.draft_email

    def test_api_exception_returns_error(self):
        p = Prospect(name="Alice", company="Acme", email="alice@acme.com")

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = RuntimeError("quota exceeded")

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            result = generate_email(
                p,
                research_notes="Some notes.",
                api_key="fake",
            )

        assert result.error is not None
        assert "quota exceeded" in result.error
