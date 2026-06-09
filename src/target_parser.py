from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re

from models import Invoice, InvoiceItem
from parser_utils import compact_line, find_money, parse_date_text, parse_decimal
from walmart_parser import ParseError


DATE_PATTERNS = [
    re.compile(r"\bOrder\s+date\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
    re.compile(r"\bOrder\s+placed\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
    re.compile(r"\bPlaced\s+on\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
]
ORDER_RE = re.compile(r"\bOrder\s*(?:number|#)\s*:?\s*([A-Za-z0-9-]+)", re.IGNORECASE)
ITEM_RE = re.compile(
    r"^(?P<name>.+?)\s+"
    r"(?:Qty|Quantity)\s*(?P<qty>\d+(?:\.\d+)?)"
    r"(?:\s+\$?-?\d+(?:,\d{3})*(?:\.\d{2})?)?"
    r"\s+\$?(?P<cost>-?\d+(?:,\d{3})*(?:\.\d{2})?)$",
    re.IGNORECASE,
)
SKIP_PREFIXES = (
    "Target",
    "Order date",
    "Order placed",
    "Placed on",
    "Order number",
    "Order #",
    "Subtotal",
    "Discount",
    "Savings",
    "Tax",
    "Total",
    "Payment",
)


def parse_invoice_text(raw_text: str, source_path: Path) -> Invoice:
    if "target" not in raw_text.lower():
        raise ParseError("Not a Target invoice")

    order_date = _parse_order_date(raw_text)
    items = _parse_items(raw_text)
    if not items:
        raise ParseError("No Target item rows found")

    return Invoice(
        source_path=source_path,
        store_name="Target",
        order_date=order_date,
        order_number=_parse_order_number(raw_text),
        items=items,
        tax=find_money(raw_text, ("Tax", "Sales tax", "Estimated tax")) or Decimal("0.00"),
        total=find_money(raw_text, ("Total", "Order total")),
        raw_text=raw_text,
    )


def _parse_order_date(raw_text: str):
    for pattern in DATE_PATTERNS:
        match = pattern.search(raw_text)
        if match:
            return parse_date_text(match.group(1), ("%B %d, %Y", "%b %d, %Y"))

    raise ParseError("Target order date not found")


def _parse_order_number(raw_text: str) -> str | None:
    match = ORDER_RE.search(raw_text)
    return match.group(1) if match else None


def _parse_items(raw_text: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for raw_line in raw_text.splitlines():
        line = compact_line(raw_line)
        if not line or line.startswith(SKIP_PREFIXES):
            continue

        match = ITEM_RE.match(line)
        if not match:
            continue

        items.append(
            InvoiceItem(
                name=match.group("name").strip(" ,-"),
                quantity=match.group("qty"),
                cost=parse_decimal(match.group("cost")),
            )
        )

    return items
