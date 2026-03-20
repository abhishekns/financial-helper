from __future__ import annotations

import re
from datetime import date, datetime

from .models import DocumentAsset, FinancialEvent

_DATE_PATTERNS = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{2}/\d{2}/\d{4})\b"),
]

_KEYWORDS = {
    "estimated tax": "estimated_tax",
    "property tax": "property_tax",
    "insurance renewal": "insurance_renewal",
    "mortgage": "loan_payment",
    "dividend": "investment_income",
    "401k": "retirement_contribution",
    "ira": "retirement_contribution",
    "tax": "tax_deadline",
}


class FinancialFactExtractorAgent:
    """Extracts candidate financial events from normalized documents."""

    def extract(self, documents: list[DocumentAsset]) -> list[FinancialEvent]:
        events: list[FinancialEvent] = []
        for document in documents:
            lowered = document.content.lower()
            due_dates = self._extract_dates(document.content)
            remaining_text = lowered
            for keyword, event_type in sorted(_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
                if keyword in remaining_text:
                    remaining_text = remaining_text.replace(keyword, " ")
                    for due_date in due_dates:
                        events.append(
                            FinancialEvent(
                                title=f"{keyword.title()} from {document.name}",
                                event_type=event_type,
                                due_date=due_date,
                                confidence=0.65,
                                source_documents=[document.name],
                                details={
                                    "keyword": keyword,
                                    "document_type": document.document_type,
                                },
                            )
                        )
        return self._deduplicate(events)

    def _extract_dates(self, text: str) -> list[date]:
        found_dates: list[date] = []
        for pattern in _DATE_PATTERNS:
            for match in pattern.findall(text):
                try:
                    parsed = datetime.strptime(match, "%Y-%m-%d").date()
                except ValueError:
                    parsed = datetime.strptime(match, "%m/%d/%Y").date()
                found_dates.append(parsed)
        return found_dates

    def _deduplicate(self, events: list[FinancialEvent]) -> list[FinancialEvent]:
        seen: set[tuple[str, date]] = set()
        deduped: list[FinancialEvent] = []
        for event in events:
            key = (event.event_type, event.due_date)
            if key not in seen:
                seen.add(key)
                deduped.append(event)
        return deduped
