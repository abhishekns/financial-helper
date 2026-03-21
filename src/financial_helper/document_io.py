from __future__ import annotations

import logging
from pathlib import Path

from .models import DocumentAsset

LOGGER = logging.getLogger(__name__)

_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}


def load_document_asset(path: str | Path) -> DocumentAsset:
    """Load a local file into a DocumentAsset.

    The starter implementation fully supports text-like files. Binary formats such
    as PDF, XLSX, and DOCX are preserved as placeholders so the UI can still show
    that a document was added while future parser integrations are pending.
    """

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in _TEXT_EXTENSIONS:
        content = file_path.read_text(encoding="utf-8")
        extraction_status = "parsed"
    else:
        content = (
            f"Document placeholder for {file_path.name}. "
            "Add a dedicated parser/OCR step to extract structured text from this file type."
        )
        extraction_status = "placeholder"

    asset = DocumentAsset(
        name=file_path.name,
        document_type=suffix.lstrip(".") or "unknown",
        content=content,
        source=str(file_path),
        metadata={
            "path": str(file_path),
            "extraction_status": extraction_status,
        },
    )
    LOGGER.info("Loaded document %s (%s)", asset.name, extraction_status)
    return asset
