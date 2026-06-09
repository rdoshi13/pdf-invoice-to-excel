from pathlib import Path

import pytest

from src import pdf_reader


def test_extract_text_uses_pdfplumber_when_text_is_present(monkeypatch):
    def fake_pdfplumber(pdf_path: Path) -> str:
        return "This is enough extracted Walmart invoice text to parse."

    monkeypatch.setattr(pdf_reader, "extract_text_with_pdfplumber", fake_pdfplumber)

    text = pdf_reader.extract_text(Path("invoice.pdf"))

    assert text == "This is enough extracted Walmart invoice text to parse."


def test_extract_text_rejects_scanned_or_low_text_pdf(monkeypatch):
    def fake_pdfplumber(pdf_path: Path) -> str:
        return "short"

    monkeypatch.setattr(pdf_reader, "extract_text_with_pdfplumber", fake_pdfplumber)

    with pytest.raises(pdf_reader.TextExtractionError, match="Scanned/image PDFs are not supported"):
        pdf_reader.extract_text(Path("invoice.pdf"))
