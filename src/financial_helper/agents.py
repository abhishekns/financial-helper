from __future__ import annotations

from datetime import date
from typing import Any

from .extraction import FinancialFactExtractorAgent
from .ingestion import DocumentIngestionAgent
from .models import DocumentAsset, Reminder
from .reminders import ReminderPlannerAgent


class FinancialAssistantSystem:
    """End-to-end starter orchestration for the financial reminder workflow."""

    def __init__(self) -> None:
        self.ingestion_agent = DocumentIngestionAgent()
        self.extractor_agent = FinancialFactExtractorAgent()
        self.reminder_agent = ReminderPlannerAgent()

    def run(self, documents: list[DocumentAsset], today: date | None = None) -> dict[str, Any]:
        current_date = today or date.today()
        normalized_documents = self.ingestion_agent.ingest(documents)
        events = self.extractor_agent.extract(normalized_documents)
        reminders = self.reminder_agent.plan(events, today=current_date)
        return {
            "documents": normalized_documents,
            "events": events,
            "reminders": reminders,
            "summary": self._summarize(reminders),
        }

    def _summarize(self, reminders: list[Reminder]) -> dict[str, int]:
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for reminder in reminders:
            summary[reminder.priority] += 1
        return summary
