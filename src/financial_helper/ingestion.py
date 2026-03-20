from __future__ import annotations

from collections.abc import Iterable

from .models import DocumentAsset


class DocumentIngestionAgent:
    """Normalizes incoming files into a unified document model.

    In a production system this agent would call OCR, spreadsheet parsers,
    and document classifiers. The starter implementation assumes content has
    already been extracted to text.
    """

    def ingest(self, documents: Iterable[DocumentAsset]) -> list[DocumentAsset]:
        normalized: list[DocumentAsset] = []
        for document in documents:
            cleaned_content = " ".join(document.content.split())
            merged_metadata = {
                "normalized": True,
                **document.metadata,
            }
            normalized.append(
                DocumentAsset(
                    name=document.name,
                    document_type=document.document_type.lower(),
                    content=cleaned_content,
                    source=document.source,
                    metadata=merged_metadata,
                )
            )
        return normalized
