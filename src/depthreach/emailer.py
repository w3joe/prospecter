"""Gemini-powered cold email generation."""

from __future__ import annotations

import sys
from typing import Optional

from .models import EmailResult, Prospect

_TONE_GUIDANCE = {
    "professional": "formal, respectful, and business-appropriate",
    "casual": "friendly, conversational, and approachable",
    "direct": "concise, to-the-point, and action-oriented",
}

_PROMPT_TEMPLATE = """\
You are an expert cold email copywriter. Write a personalized cold email for the following prospect.

Prospect details:
- Name: {name}
- Email: {email}
- Company: {company}

Research notes:
{research_notes}

Requirements:
- Tone: {tone_guidance}
- Reference at least 2 specific details from the research notes
- Keep the email under 200 words
- Include a clear, single call-to-action
- Do NOT use placeholders like [Your Name] – write the email body only (no subject line, no sign-off with placeholders)
- Be genuine and avoid generic sales clichés

Write only the email body text, nothing else.
"""


def generate_email(
    prospect: Prospect,
    research_notes: str,
    api_key: str,
    tone: str = "professional",
    verbose: bool = False,
) -> EmailResult:
    """Generate a cold email using Google Gemini 2.5 Flash-Lite Preview.

    Args:
        prospect: The prospect to email.
        research_notes: Research notes gathered for this prospect.
        api_key: Google Gemini API key.
        tone: One of 'professional', 'casual', 'direct'.
        verbose: If True, print progress to stderr.

    Returns:
        EmailResult with the draft email (or an error message).
    """
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError as exc:
        return EmailResult(
            prospect=prospect,
            research_notes=research_notes,
            draft_email="",
            error=f"google-generativeai is not installed: {exc}",
        )

    tone_guidance = _TONE_GUIDANCE.get(tone, _TONE_GUIDANCE["professional"])
    prompt = _PROMPT_TEMPLATE.format(
        name=prospect.name,
        email=prospect.email or "(not provided)",
        company=prospect.company or "(not provided)",
        research_notes=research_notes or "No research available.",
        tone_guidance=tone_guidance,
    )

    if verbose:
        print(
            f"[email] Generating email for: {prospect.display_name()}", file=sys.stderr
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
        response = model.generate_content(prompt)
        draft = response.text.strip()
        return EmailResult(
            prospect=prospect,
            research_notes=research_notes,
            draft_email=draft,
        )
    except Exception as exc:  # noqa: BLE001
        return EmailResult(
            prospect=prospect,
            research_notes=research_notes,
            draft_email="",
            error=f"Email generation failed: {exc}",
        )
