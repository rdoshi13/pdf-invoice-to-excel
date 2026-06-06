from __future__ import annotations

from pathlib import Path

import pdfplumber


def extract_text(pdf_path: Path) -> str:
    page_texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text)

    return "\n".join(page_texts).strip()
