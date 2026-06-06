from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass
class InvoiceItem:
    name: str
    cost: Decimal
    quantity: str | None = None
    status: str | None = None


@dataclass
class Invoice:
    source_path: Path
    order_date: date
    order_number: str | None
    items: list[InvoiceItem]
    tax: Decimal
    total: Decimal | None
    raw_text: str


@dataclass
class ProcessingResult:
    found_pdf_count: int
    parsed_count: int
    failed_files: list[Path]
    added_sheets: list[str]
    output_path: Path
