# financial-helper

An agentic AI starter system that helps users stay ahead of critical financial dates, taxes, investments, and recurring obligations by learning from uploaded financial history.

## What this system should do

The user can upload spreadsheets, PDFs, tax documents, statements, notices, and notes. The system should:

1. ingest heterogeneous files,
2. extract financial facts and due dates,
3. infer which deadlines recur or matter most,
4. generate reminders with priority and rationale,
5. deliver those reminders through email, SMS, calendar, or in-app notifications.

## How users will use it

### Current starter flow
1. Launch the desktop app.
2. Click **Add Files** to upload personal financial documents, or **Add Sample Docs** to try the demo.
3. Click **Analyze** to generate reminder candidates from the uploaded history.
4. Review the reminder list, due dates, and rationale.
5. Use the **Workflows** tab to decide what to do next, such as prioritizing taxes, payments, or investment follow-ups.

### What the UI supports today
- Adding local files from a desktop file picker.
- Loading a sample dataset to demonstrate the workflow.
- Reviewing uploaded document details and extraction status.
- Generating a reminder list from normalized document text.
- Seeing suggested next-step workflows after analysis.

### What is planned next
- Native parsing for PDF, DOCX, XLSX, and scanned images.
- Reminder approval before syncing to external channels.
- Calendar/email/SMS integrations.
- Persistent history so the system can learn recurring obligations over time.

## Recommended agentic architecture

### 1. Intake and document understanding
- **Document ingestion agent**
  - Accepts PDFs, Excel, CSV, Word documents, scanned images, and emails.
  - Uses OCR and parsers to turn each file into normalized text plus metadata.
  - Tags source type, upload date, account/institution, and confidence.

### 2. Financial fact extraction
- **Financial fact extractor agent**
  - Identifies dates, amounts, entities, account types, tax forms, and investment events.
  - Maps raw text into normalized event types such as `tax_deadline`, `estimated_tax`, `retirement_contribution`, `property_tax`, `loan_payment`, and `investment_income`.
  - Stores provenance so every reminder can point back to supporting source documents.

### 3. Timeline and memory
- **Financial memory agent**
  - Builds a user timeline from historical documents.
  - Detects recurring patterns like quarterly taxes, annual IRA contributions, mortgage renewals, insurance renewals, dividend schedules, and employer stock vesting dates.
  - Maintains a profile of user preferences, filing cadence, institutions, and reminder lead times.

### 4. Reminder planning and actioning
- **Reminder planner agent**
  - Converts extracted events into reminders.
  - Assigns urgency using due date proximity, event type, and historical importance.
  - Produces reminder text, rationale, and suggested next actions.

- **Notification/action agent**
  - Sends reminders to downstream channels.
  - Can create calendar events, draft emails, or suggest a checklist for the next step.

### 5. Human-in-the-loop safety
- Require user confirmation before high-impact actions.
- Show source citations for every extracted deadline.
- Let users correct event types and dates so the system improves over time.
- Separate “detected from document” from “inferred from history”.

## Minimal data model

```text
DocumentAsset
  - name
  - document_type
  - content
  - metadata

FinancialEvent
  - title
  - event_type
  - due_date
  - confidence
  - source_documents
  - details

Reminder
  - title
  - due_date
  - message
  - priority
  - rationale
```

## Included starter implementation

This repository now includes a lightweight Python scaffold that demonstrates the core workflow:

- `DocumentIngestionAgent` normalizes incoming document text.
- `FinancialFactExtractorAgent` finds financial keywords plus explicit dates.
- `ReminderPlannerAgent` prioritizes upcoming events.
- `FinancialAssistantSystem` orchestrates the full pipeline.
- `FinancialHelperApp` provides a Tkinter desktop UI for uploading files and reviewing reminders.
- `load_document_asset` converts local files into `DocumentAsset` instances for the desktop flow.

## Running the application

### Run the desktop UI
```bash
python -m financial_helper.ui
```

### Run the demo pipeline in Python
```python
from datetime import date

from financial_helper import DocumentAsset, FinancialAssistantSystem

system = FinancialAssistantSystem()
documents = [
    DocumentAsset(
        name="tax-planner.pdf",
        document_type="pdf",
        content="Estimated tax payment due 2026-04-15 and IRA contribution due 04/15/2026",
    )
]

result = system.run(documents, today=date(2026, 3, 20))
for reminder in result["reminders"]:
    print(reminder.priority, reminder.message)
```

## Possible user workflows

### Workflow 1: Annual tax preparation
- Upload prior-year returns, quarterly estimate worksheets, and accountant notes.
- Review extracted filing and payment dates.
- Confirm the next tax deadlines and later sync them into a calendar.

### Workflow 2: Investment maintenance
- Upload brokerage statements, dividend summaries, and vesting schedules.
- Detect expected income events or contribution deadlines.
- Prioritize actions such as reinvestment reviews or contribution windows.

### Workflow 3: Household recurring obligations
- Upload mortgage notices, property tax bills, insurance renewals, and HOA statements.
- Build a single timeline of recurring household obligations.
- Use the reminder list as the basis for an operations checklist.

## GitHub workflows included

Three GitHub Actions workflows are included for automation:

1. **build-package**: runs tests and builds source/wheel artifacts for normal pushes and pull requests.
2. **build-application**: runs tests and bundles the Tkinter app with PyInstaller for normal pushes and pull requests.
3. **release**: when you push a Git tag matching `vX.X.X` such as `v1.2.0`, GitHub Actions rebuilds both deliverables, reruns tests in both build jobs, and publishes a GitHub release with the package and desktop app attached as release assets.

## Suggested production stack

- **API**: FastAPI or Django Ninja
- **Workflow orchestration**: Temporal, Prefect, or Celery
- **LLM extraction/classification**: OpenAI structured outputs + retrieval over uploaded documents
- **Storage**: Postgres for normalized facts, object storage for files, vector DB only if semantic retrieval is needed
- **Notifications**: SendGrid, Twilio, Google Calendar, Slack
- **Parsing/OCR**: Apache Tika, unstructured, pandas/openpyxl, OCR pipeline for scanned PDFs

## Important compliance and trust considerations

- Financial reminders can affect taxes and investments, so keep auditable provenance.
- Encrypt source files and sensitive extracted fields.
- Support retention and deletion controls.
- Avoid giving tax or investment advice unless explicitly designed, reviewed, and compliant.
- Log when an event was extracted versus inferred.

## Next steps I recommend

1. Add parsers for PDF, XLSX, CSV, and DOCX inputs.
2. Replace keyword extraction with structured LLM extraction plus rule validation.
3. Persist normalized events and reminder history in a database.
4. Add user-configurable channels and lead times.
5. Build a review UI where users confirm or edit detected reminders.
