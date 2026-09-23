"""
Document loading layer.

WHAT: Reads company documents from disk and returns them as plain text plus
      metadata (source filename, document type, and page number where the
      file format has pages).
WHY:  The rest of the RAG pipeline (chunker, embedder, vector store) should
      never touch the filesystem or know about file formats. Isolating
      loading here means chunking/embedding/retrieval logic is unaffected by
      adding a new file format later.
HOW:  A `LoadedDocument` dataclass carries `text` + `metadata`. Loading is
      dispatched by file extension through a small registry
      (`_LOADERS_BY_EXTENSION`), so supporting a new extension means adding
      one function and one registry entry — not modifying the loop that
      walks the documents directory.
ALTERNATIVE: a single function with if/elif branches per extension. Rejected
      because it does not scale cleanly and mixes "how to walk a directory"
      with "how to parse one file format".

CURRENT SUPPORT: .txt (used by the assessment's synthetic documents).
PDF READINESS: `load_pdf_document` below is a real, working implementation
      (using `pypdf`, already a transitive dependency of `chromadb`) that
      preserves per-page text and page numbers in metadata. It is registered
      in `_LOADERS_BY_EXTENSION` so dropping a .pdf file into `documents/`
      works today without any architecture change — nothing needed to be
      deferred to "PDF support later".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


class DocumentLoadError(Exception):
    """Raised when the documents directory or a document cannot be read."""


@dataclass
class LoadedDocument:
    """One unit of loaded text plus the metadata that must survive chunking.

    For a .txt file this is the whole file as one LoadedDocument (page=None).
    For a .pdf file, one LoadedDocument is produced PER PAGE, so page numbers
    can be attached to chunks later without the chunker needing to know
    anything about PDFs.
    """

    text: str
    source: str  # filename, e.g. "leave_policy.txt" — never a full path
    document_type: str  # derived from filename, e.g. "leave_policy"
    page: Optional[int] = None  # 1-indexed; None when the format has no pages
    extra_metadata: Dict[str, str] = field(default_factory=dict)


def _document_type_from_filename(filename: str) -> str:
    """WHAT: derive a human-readable document type from the filename.
    WHY: chunk metadata should say *what kind* of document a chunk came
    from (e.g. "leave_policy") without requiring a manual mapping table
    that would need updating every time a document is added.
    """
    return Path(filename).stem


def _normalize_whitespace(text: str) -> str:
    """Conservative text normalization — see docs/ARCHITECTURE.md.

    WHAT: collapses runs of 3+ blank lines to a single blank line, and
    strips trailing whitespace from each line. Leaves headings, numbering,
    and policy wording completely untouched.
    WHY: the assessment requires the RAG system to retrieve the *actual*
    document content — aggressive normalization (e.g. lowercasing,
    stripping punctuation, collapsing all whitespace to single spaces)
    risks altering meaning or making retrieved chunks look garbled when
    shown to the user as grounded context.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    normalized_lines: List[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip() + "\n"


def load_txt_document(path: Path) -> List[LoadedDocument]:
    """Load a single .txt file as one LoadedDocument."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError(f"{path.name}: not valid UTF-8 text") from exc

    text = _normalize_whitespace(raw_text)
    if not text.strip():
        raise DocumentLoadError(f"{path.name}: file is empty after normalization")

    return [
        LoadedDocument(
            text=text,
            source=path.name,
            document_type=_document_type_from_filename(path.name),
            page=None,
        )
    ]


def load_pdf_document(path: Path) -> List[LoadedDocument]:
    """Load a .pdf file, one LoadedDocument per page (page numbers preserved).

    Uses `pypdf` — a small, single-purpose, pure-Python PDF text-extraction
    library (added explicitly to backend/requirements.txt for this).
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - environment issue, not logic
        raise DocumentLoadError(
            f"{path.name}: PDF support requires 'pypdf'. Run "
            "`pip install pypdf` (already in backend/requirements.txt)."
        ) from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pragma: no cover - depends on malformed input
        raise DocumentLoadError(f"{path.name}: could not be read as a PDF") from exc

    documents: List[LoadedDocument] = []
    document_type = _document_type_from_filename(path.name)
    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = _normalize_whitespace(raw_text)
        if not text.strip():
            continue  # skip genuinely empty pages (e.g. a blank divider page)
        documents.append(
            LoadedDocument(
                text=text,
                source=path.name,
                document_type=document_type,
                page=page_number,
            )
        )

    if not documents:
        raise DocumentLoadError(f"{path.name}: no extractable text found in any page")

    return documents


_LOADERS_BY_EXTENSION: Dict[str, Callable[[Path], List[LoadedDocument]]] = {
    ".txt": load_txt_document,
    ".pdf": load_pdf_document,
}


def load_documents(documents_directory: str) -> List[LoadedDocument]:
    """Load every supported file under `documents_directory`.

    Raises DocumentLoadError if the directory is missing, contains no
    supported files, or a specific file fails to load. Fails clearly
    rather than silently skipping problems, per the assessment's error
    handling requirements.
    """
    directory = Path(documents_directory)
    if not directory.exists():
        raise DocumentLoadError(f"Documents directory not found: {directory}")
    if not directory.is_dir():
        raise DocumentLoadError(f"Not a directory: {directory}")

    all_documents: List[LoadedDocument] = []
    skipped_unsupported: List[str] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        loader = _LOADERS_BY_EXTENSION.get(path.suffix.lower())
        if loader is None:
            skipped_unsupported.append(path.name)
            continue
        all_documents.extend(loader(path))

    if not all_documents:
        raise DocumentLoadError(
            f"No supported documents found in {directory} "
            f"(supported extensions: {sorted(_LOADERS_BY_EXTENSION)})"
        )

    return all_documents
