from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class DocumentAsset:
    """A user supplied file and its extracted metadata."""

    name: str
    document_type: str
    content: str
    source: str = "upload"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FinancialEvent:
    """A normalized financial fact discovered from user history."""

    title: str
    event_type: str
    due_date: date
    confidence: float
    source_documents: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Reminder:
    """An actionable reminder generated for the user."""

    title: str
    due_date: date
    message: str
    priority: str
    rationale: str
