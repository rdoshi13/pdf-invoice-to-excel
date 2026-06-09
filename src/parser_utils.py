from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import re


MONEY_PATTERN = r"-?\$?\s*\d+(?:,\d{3})*(?:\.\d{2})?"


def parse_decimal(value: str) -> Decimal:
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def parse_date_text(value: str, formats: tuple[str, ...]) -> datetime.date:
    cleaned = " ".join(value.split()).strip(", ")
    for date_format in formats:
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Date format not supported: {value}")


def find_money(raw_text: str, labels: tuple[str, ...]) -> Decimal | None:
    for label in labels:
        match = re.search(rf"\b{label}\s*:?\s*({MONEY_PATTERN})\b", raw_text, re.IGNORECASE)
        if match:
            return parse_decimal(match.group(1))

    return None


def compact_line(line: str) -> str:
    return " ".join(line.split())
