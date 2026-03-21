from __future__ import annotations

import re
from datetime import date, datetime

try:
    from dateparser.search import search_dates

    _DATEPARSER_AVAILABLE = True
except ImportError:
    search_dates = None
    _DATEPARSER_AVAILABLE = False

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

_ALPHA_DATE_TOKENS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "jan",
    "january",
    "feb",
    "february",
    "mar",
    "march",
    "apr",
    "april",
    "may",
    "jun",
    "june",
    "jul",
    "july",
    "aug",
    "august",
    "sep",
    "sept",
    "september",
    "oct",
    "october",
    "nov",
    "november",
    "dec",
    "december",
    "today",
    "tomorrow",
    "yesterday",
}


class FinancialFactExtractorAgent:
    """Extracts candidate financial events from normalized documents."""

    def extract(self, documents: list[DocumentAsset], today: date | None = None) -> list[FinancialEvent]:
        base_date = today or date.today()
        events: list[FinancialEvent] = []
        for document in documents:
            lowered = document.content.lower()
            due_dates = self._extract_dates(document.content, base_date)
            remaining_text = lowered
            for keyword, event_type in sorted(_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
                if keyword in remaining_text:
                    remaining_text = remaining_text.replace(keyword, " ")
                    for due_date, matched_text, parser in due_dates:
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
                                    "matched_text": matched_text,
                                    "parser": parser,
                                },
                            )
                        )
        return self._deduplicate(events)

    def _extract_dates(self, text: str, base_date: date) -> list[tuple[date, str, str]]:
        found_dates: list[tuple[date, str, str]] = []
        regex_dates = self._extract_dates_with_regex(text)
        regex_texts = {match_text for _, match_text, _ in regex_dates}
        if _DATEPARSER_AVAILABLE and search_dates is not None:
            parser_dates = self._extract_dates_with_dateparser(text, base_date)
            parser_dates = [
                (due_date, match_text, parser)
                for due_date, match_text, parser in parser_dates
                if match_text not in regex_texts
            ]
            found_dates.extend(parser_dates)
        found_dates.extend(regex_dates)
        return self._dedupe_date_matches(found_dates)

    def _extract_dates_with_dateparser(self, text: str, base_date: date) -> list[tuple[date, str, str]]:
        settings = {
            "RELATIVE_BASE": datetime.combine(base_date, datetime.min.time()),
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "STRICT_PARSING": False,
        }
        matches = (search_dates(text, settings=settings) or [])
        settings["DATE_ORDER"] = "MDY"
        matches.extend(search_dates(text, settings=settings) or [])
        parsed: list[tuple[date, str, str]] = []
        for match_text, parsed_dt in matches:
            if not self._should_keep_dateparser_match(match_text):
                continue
            parsed.append((parsed_dt.date(), match_text, "dateparser"))
        return parsed

    def _extract_dates_with_regex(self, text: str) -> list[tuple[date, str, str]]:
        found_dates: list[tuple[date, str, str]] = []
        for pattern in _DATE_PATTERNS:
            for match in pattern.findall(text):
                try:
                    parsed = datetime.strptime(match, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        parsed = datetime.strptime(match, "%d/%m/%Y").date()
                    except ValueError:
                        parsed = datetime.strptime(match, "%m/%d/%Y").date()
                found_dates.append((parsed, match, "regex"))
        return found_dates

    def _should_keep_dateparser_match(self, match_text: str) -> bool:
        if any(char.isdigit() for char in match_text):
            return True
        normalized = match_text.strip().lower()
        return any(token in normalized for token in _ALPHA_DATE_TOKENS)

    def _dedupe_date_matches(self, matches: list[tuple[date, str, str]]) -> list[tuple[date, str, str]]:
        seen: set[tuple[date, str]] = set()
        deduped: list[tuple[date, str, str]] = []
        for due_date, match_text, parser in matches:
            key = (due_date, match_text)
            if key in seen:
                continue
            seen.add(key)
            deduped.append((due_date, match_text, parser))
        return deduped

    def _deduplicate(self, events: list[FinancialEvent]) -> list[FinancialEvent]:
        seen: set[tuple[str, date]] = set()
        deduped: list[FinancialEvent] = []
        for event in events:
            key = (event.event_type, event.due_date)
            if key not in seen:
                seen.add(key)
                deduped.append(event)
        return deduped
