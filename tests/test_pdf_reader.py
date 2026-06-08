from pathlib import Path

from src import pdf_reader


def test_extract_text_uses_pdfplumber_when_text_is_present(monkeypatch):
    calls = {"ocr": 0}

    def fake_pdfplumber(pdf_path: Path) -> str:
        return "This is enough extracted Walmart invoice text to skip OCR."

    def fake_ocr(pdf_path: Path) -> str:
        calls["ocr"] += 1
        return "ocr text"

    monkeypatch.setattr(pdf_reader, "extract_text_with_pdfplumber", fake_pdfplumber)
    monkeypatch.setattr(pdf_reader, "extract_text_with_ocr", fake_ocr)

    text = pdf_reader.extract_text(Path("invoice.pdf"))

    assert text == "This is enough extracted Walmart invoice text to skip OCR."
    assert calls["ocr"] == 0


def test_extract_text_falls_back_to_ocr_when_pdf_text_is_short(monkeypatch):
    def fake_pdfplumber(pdf_path: Path) -> str:
        return "short"

    def fake_ocr(pdf_path: Path) -> str:
        return "OCR extracted Walmart invoice text"

    monkeypatch.setattr(pdf_reader, "extract_text_with_pdfplumber", fake_pdfplumber)
    monkeypatch.setattr(pdf_reader, "extract_text_with_ocr", fake_ocr)

    text = pdf_reader.extract_text(Path("invoice.pdf"))

    assert text == "OCR extracted Walmart invoice text"


def test_extract_text_returns_short_pdf_text_if_ocr_finds_nothing(monkeypatch):
    def fake_pdfplumber(pdf_path: Path) -> str:
        return "short"

    def fake_ocr(pdf_path: Path) -> str:
        return ""

    monkeypatch.setattr(pdf_reader, "extract_text_with_pdfplumber", fake_pdfplumber)
    monkeypatch.setattr(pdf_reader, "extract_text_with_ocr", fake_ocr)

    text = pdf_reader.extract_text(Path("invoice.pdf"))

    assert text == "short"
