from __future__ import annotations

import logging
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .agents import FinancialAssistantSystem
from .document_io import load_document_asset
from .models import DocumentAsset

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    _DND_AVAILABLE = False


LOGGER = logging.getLogger(__name__)


class FinancialHelperApp:
    """Simple Tkinter UI for uploading documents and reviewing reminders."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Financial Helper")
        self.root.geometry("1100x720")
        self.system = FinancialAssistantSystem()
        self.documents: list[DocumentAsset] = []
        self.drag_drop_available = _DND_AVAILABLE

        self._build_layout()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=16)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Financial Helper",
            font=("TkDefaultFont", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=(
                "Upload financial files, review extracted reminders, and use the workflow "
                "guide to decide what to do next."
            ),
            wraplength=900,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        controls = ttk.Frame(self.root, padding=(16, 0, 16, 16))
        controls.grid(row=1, column=0, sticky="nsew")
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(2, weight=1)

        actions = ttk.Frame(controls)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for index in range(4):
            actions.columnconfigure(index, weight=1)

        ttk.Button(actions, text="Add Files", command=self.add_files).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(actions, text="Add Sample Docs", command=self.add_sample_documents).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(actions, text="Analyze", command=self.analyze_documents).grid(row=0, column=2, sticky="ew", padx=8)
        ttk.Button(actions, text="Clear", command=self.clear_documents).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        label_text = "Uploaded documents"
        if self.drag_drop_available:
            label_text += " (drag and drop files here)"
        ttk.Label(controls, text=label_text).grid(row=1, column=0, sticky="w")
        self.document_list = tk.Listbox(controls, height=12)
        self.document_list.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        if self.drag_drop_available:
            self.document_list.drop_target_register(DND_FILES)
            self.document_list.dnd_bind("<<Drop>>", self._handle_drop)

        detail_notebook = ttk.Notebook(self.root)
        detail_notebook.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))

        self.reminders_text = tk.Text(detail_notebook, wrap="word")
        self.workflows_text = tk.Text(detail_notebook, wrap="word")
        self.documents_text = tk.Text(detail_notebook, wrap="word")
        for widget in (self.reminders_text, self.workflows_text, self.documents_text):
            widget.configure(state="disabled")

        detail_notebook.add(self.reminders_text, text="Reminders")
        detail_notebook.add(self.workflows_text, text="Workflows")
        detail_notebook.add(self.documents_text, text="Document details")

        self._set_text(
            self.workflows_text,
            self._default_workflow_guide(),
        )
        self._set_text(
            self.reminders_text,
            "No analysis yet. Add one or more documents, then click Analyze.",
        )
        self._set_text(
            self.documents_text,
            "Supported immediately: .txt, .md, .csv, .json, .log\n"
            "Planned next: PDF, DOCX, XLSX, scanned images via parser/OCR integrations.",
        )

    def add_files(self) -> None:
        selected_files = filedialog.askopenfilenames(
            title="Select financial files",
            filetypes=[("All files", "*.*")],
        )
        self._add_assets_from_paths(selected_files)

    def add_sample_documents(self) -> None:
        sample_documents = [
            DocumentAsset(
                name="estimated-tax.txt",
                document_type="txt",
                content="Estimated tax payment due 2026-04-15 and IRA contribution due 04/15/2026.",
                metadata={"extraction_status": "sample"},
            ),
            DocumentAsset(
                name="mortgage-review.txt",
                document_type="txt",
                content="Mortgage autopay review before 2026-05-01.",
                metadata={"extraction_status": "sample"},
            ),
        ]
        for asset in sample_documents:
            self.documents.append(asset)
            self.document_list.insert(tk.END, f"{asset.name} ({asset.metadata.get('extraction_status')})")
        self._refresh_document_details()

    def analyze_documents(self) -> None:
        if not self.documents:
            messagebox.showinfo("Financial Helper", "Add at least one document before analyzing.")
            return

        LOGGER.info("Analyzing %s documents", len(self.documents))
        result = self.system.run(self.documents)
        reminder_lines = []
        for reminder in result["reminders"]:
            reminder_lines.append(
                f"[{reminder.priority.upper()}] {reminder.title}\n"
                f"Due: {reminder.due_date.isoformat()}\n"
                f"Message: {reminder.message}\n"
                f"Why: {reminder.rationale}"
            )
        if not reminder_lines:
            reminder_lines.append("No future reminders were generated from the current document set.")

        self._set_text(self.reminders_text, "\n\n".join(reminder_lines))
        self._set_text(self.workflows_text, self._workflow_guide_for_results(result["summary"]))
        self._refresh_document_details()

    def clear_documents(self) -> None:
        self.documents.clear()
        self.document_list.delete(0, tk.END)
        self._set_text(self.reminders_text, "No analysis yet. Add one or more documents, then click Analyze.")
        self._set_text(self.workflows_text, self._default_workflow_guide())
        self._refresh_document_details()

    def _refresh_document_details(self) -> None:
        if not self.documents:
            body = "No documents loaded. Use Add Files for your own history or Add Sample Docs for a demo."
        else:
            lines = []
            for asset in self.documents:
                source = asset.metadata.get("path", asset.source)
                lines.append(
                    f"- {asset.name}\n"
                    f"  type: {asset.document_type}\n"
                    f"  source: {source}\n"
                    f"  extraction status: {asset.metadata.get('extraction_status', 'unknown')}\n"
                    f"  preview: {asset.content[:180]}"
                )
            body = "\n\n".join(lines)
        self._set_text(self.documents_text, body)

    def _handle_drop(self, event: tk.Event) -> None:
        paths = self._parse_drop_files(event.data)
        if not paths:
            return
        self._add_assets_from_paths(paths)

    def _parse_drop_files(self, data: str) -> list[str]:
        if not data:
            return []
        matches = re.findall(r"{([^}]*)}|(\S+)", data)
        paths = [match[0] or match[1] for match in matches]
        return [path for path in paths if path]

    def _add_assets_from_paths(self, paths: list[str] | tuple[str, ...]) -> None:
        if not paths:
            return
        for file_path in paths:
            try:
                asset = load_document_asset(file_path)
            except OSError as exc:
                LOGGER.warning("Failed to load document: %s", file_path, exc_info=exc)
                messagebox.showwarning("Financial Helper", f"Could not load {file_path}")
                continue
            self.documents.append(asset)
            self.document_list.insert(tk.END, f"{asset.name} ({asset.metadata.get('extraction_status')})")
        self._refresh_document_details()

    def _default_workflow_guide(self) -> str:
        return (
            "Suggested workflow\n"
            "1. Add your documents or try the sample set.\n"
            "2. Review extracted reminders and confirm the detected dates.\n"
            "3. Follow up on critical items first, especially tax and payment deadlines.\n"
            "4. In a future version, sync confirmed items to email, SMS, or your calendar."
        )

    def _workflow_guide_for_results(self, summary: dict[str, int]) -> str:
        return (
            "Recommended next actions\n"
            f"- Critical reminders: {summary['critical']}\n"
            f"- High-priority reminders: {summary['high']}\n"
            f"- Medium-priority reminders: {summary['medium']}\n"
            f"- Low-priority reminders: {summary['low']}\n\n"
            "Possible workflows to add next\n"
            "- Approve reminders and create calendar events.\n"
            "- Assign account owner or household member.\n"
            "- Capture corrected dates and train future extraction rules.\n"
            "- Send a weekly digest of new obligations."
        )

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if _DND_AVAILABLE and TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        if not _DND_AVAILABLE:
            LOGGER.info("Drag-and-drop disabled (tkinterdnd2 not installed)")
        root = tk.Tk()
    FinancialHelperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
