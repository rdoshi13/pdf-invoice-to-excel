from __future__ import annotations

from pathlib import Path

import pdfplumber


MIN_EXTRACTED_TEXT_LENGTH = 40


class TextExtractionError(ValueError):
    pass


def extract_text(pdf_path: Path) -> str:
    extracted_text = extract_text_with_pdfplumber(pdf_path)
    if len(extracted_text) >= MIN_EXTRACTED_TEXT_LENGTH:
        return extracted_text

    raise TextExtractionError(
        f"{pdf_path} does not contain enough embedded text to parse. "
        "Scanned/image PDFs are not supported by the CLI version."
    )


def extract_text_with_pdfplumber(pdf_path: Path) -> str:
    page_texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text)

    return "\n".join(page_texts).strip()
