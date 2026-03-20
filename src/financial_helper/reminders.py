from __future__ import annotations

from datetime import date

from .models import FinancialEvent, Reminder


class ReminderPlannerAgent:
    """Transforms extracted events into reminders with priorities."""

    def plan(self, events: list[FinancialEvent], today: date) -> list[Reminder]:
        reminders: list[Reminder] = []
        for event in sorted(events, key=lambda item: item.due_date):
            delta = (event.due_date - today).days
            if delta < 0:
                continue
            priority = self._priority_for(delta, event.event_type)
            reminders.append(
                Reminder(
                    title=event.title,
                    due_date=event.due_date,
                    message=self._message_for(event, delta),
                    priority=priority,
                    rationale=(
                        f"Detected a {event.event_type} from {', '.join(event.source_documents)} "
                        f"with {delta} day(s) remaining."
                    ),
                )
            )
        return reminders

    def _priority_for(self, days_until_due: int, event_type: str) -> str:
        if days_until_due <= 7:
            return "critical"
        if event_type in {"tax_deadline", "estimated_tax", "property_tax"} and days_until_due <= 30:
            return "high"
        if days_until_due <= 45:
            return "medium"
        return "low"

    def _message_for(self, event: FinancialEvent, days_until_due: int) -> str:
        return (
            f"{event.title} is due on {event.due_date.isoformat()} "
            f"({days_until_due} day(s) away). Review the source document and confirm the amount."
        )
