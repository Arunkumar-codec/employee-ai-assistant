"""
Tests for app.rag.loader.

Uses tmp_path to build small fake "documents/" directories rather than
touching the real documents/ folder, so these tests are independent of
whatever real company documents exist.
"""
import pytest

from app.rag.loader import DocumentLoadError, load_documents, load_txt_document


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_load_txt_document_returns_one_document_with_metadata(tmp_path):
    file_path = _write(tmp_path / "leave_policy.txt", "LEAVE POLICY\n\n1. Annual Leave\n18 days.\n")
    docs = load_txt_document(file_path)

    assert len(docs) == 1
    assert docs[0].source == "leave_policy.txt"
    assert docs[0].document_type == "leave_policy"
    assert docs[0].page is None
    assert "18 days" in docs[0].text


def test_load_documents_reads_all_txt_files_in_directory(tmp_path):
    _write(tmp_path / "a_policy.txt", "Policy A content.")
    _write(tmp_path / "b_policy.txt", "Policy B content.")

    docs = load_documents(str(tmp_path))

    sources = {doc.source for doc in docs}
    assert sources == {"a_policy.txt", "b_policy.txt"}


def test_load_documents_missing_directory_raises_clear_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(DocumentLoadError):
        load_documents(str(missing))


def test_load_documents_empty_directory_raises_clear_error(tmp_path):
    with pytest.raises(DocumentLoadError):
        load_documents(str(tmp_path))


def test_load_documents_ignores_unsupported_file_types(tmp_path):
    _write(tmp_path / "notes.md", "some markdown, not a supported type")
    _write(tmp_path / "real_policy.txt", "Real policy content.")

    docs = load_documents(str(tmp_path))

    assert len(docs) == 1
    assert docs[0].source == "real_policy.txt"


def test_load_txt_document_normalizes_excessive_blank_lines(tmp_path):
    file_path = _write(
        tmp_path / "spacey.txt", "Heading\n\n\n\n\nBody text.\n\n\n\nMore body text.\n"
    )
    docs = load_txt_document(file_path)

    # No run of 2+ consecutive blank lines should survive normalization.
    assert "\n\n\n" not in docs[0].text


def test_load_txt_document_empty_file_raises_clear_error(tmp_path):
    file_path = _write(tmp_path / "empty.txt", "   \n\n  \n")
    with pytest.raises(DocumentLoadError):
        load_txt_document(file_path)
