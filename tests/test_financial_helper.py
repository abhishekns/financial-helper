from datetime import date
from pathlib import Path

from financial_helper import DocumentAsset, FinancialAssistantSystem, load_document_asset


def test_end_to_end_generates_tax_and_investment_reminders() -> None:
    system = FinancialAssistantSystem()
    documents = [
        DocumentAsset(
            name="tax-planner.pdf",
            document_type="pdf",
            content="Estimated tax payment due 2026-04-15 and IRA contribution due 04/15/2026",
        ),
        DocumentAsset(
            name="mortgage-notes.docx",
            document_type="docx",
            content="Mortgage autopay review before 2026-05-01",
        ),
    ]

    result = system.run(documents, today=date(2026, 3, 20))

    assert len(result["events"]) == 3
    assert len(result["reminders"]) == 3
    assert result["summary"]["high"] == 1
    assert result["summary"]["medium"] == 2
    titles = {reminder.title for reminder in result["reminders"]}
    assert "Estimated Tax from tax-planner.pdf" in titles
    assert "Ira from tax-planner.pdf" in titles
    assert "Mortgage from mortgage-notes.docx" in titles


def test_load_document_asset_reads_plain_text_files(tmp_path: Path) -> None:
    sample_file = tmp_path / "tax-notes.txt"
    sample_file.write_text("Property tax due 2026-06-01", encoding="utf-8")

    document = load_document_asset(sample_file)

    assert document.name == "tax-notes.txt"
    assert document.document_type == "txt"
    assert document.metadata["extraction_status"] == "parsed"
    assert "Property tax due 2026-06-01" in document.content


def test_load_document_asset_marks_binary_files_as_placeholders(tmp_path: Path) -> None:
    sample_file = tmp_path / "statement.pdf"
    sample_file.write_bytes(b"%PDF-1.4")

    document = load_document_asset(sample_file)

    assert document.document_type == "pdf"
    assert document.metadata["extraction_status"] == "placeholder"
    assert "Document placeholder" in document.content
