"""Data models for DepthReach."""

from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass
class Prospect:
    """A single prospect to be researched and emailed."""

    name: str
    email: str = ""
    company: str = ""
    linkedin_url: str = ""
    # extra fields from CSV/JSON are preserved here
    extra: dict = dataclasses.field(default_factory=dict)

    def display_name(self) -> str:
        parts = [self.name]
        if self.company:
            parts.append(f"at {self.company}")
        return " ".join(parts)


@dataclasses.dataclass
class ResearchResult:
    """Research notes gathered for a prospect."""

    prospect: Prospect
    notes: str
    raw_results: list = dataclasses.field(default_factory=list)
    error: Optional[str] = None


@dataclasses.dataclass
class EmailResult:
    """Generated cold email for a prospect."""

    prospect: Prospect
    research_notes: str
    draft_email: str
    error: Optional[str] = None
