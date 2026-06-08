from __future__ import annotations

from pathlib import Path

from pdf2image import convert_from_path
import pdfplumber
import pytesseract


MIN_EXTRACTED_TEXT_LENGTH = 40
OCR_DPI = 300


def extract_text(pdf_path: Path) -> str:
    extracted_text = extract_text_with_pdfplumber(pdf_path)
    if len(extracted_text) >= MIN_EXTRACTED_TEXT_LENGTH:
        return extracted_text

    ocr_text = extract_text_with_ocr(pdf_path)
    return ocr_text or extracted_text


def extract_text_with_pdfplumber(pdf_path: Path) -> str:
    page_texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text)

    return "\n".join(page_texts).strip()


def extract_text_with_ocr(pdf_path: Path) -> str:
    page_texts: list[str] = []
    for page_image in convert_from_path(pdf_path, dpi=OCR_DPI):
        text = pytesseract.image_to_string(page_image) or ""
        if text.strip():
            page_texts.append(text)

    return "\n".join(page_texts).strip()
