from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from models import Invoice, InvoiceItem


DATE_RE = re.compile(r"\b([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})\s+order\b")
ORDER_RE = re.compile(r"\bOrder#\s*([A-Za-z0-9-]+)")
MONEY_RE_TEMPLATE = r"\b{label}\s+\$(-?\d+(?:,\d{{3}})*(?:\.\d{{2}})?)"
ITEM_RE = re.compile(
    r"^(?P<body>.+?)\s+"
    r"Qty\s*(?P<qty>\d+(?:\.\d+)?)"
    r"\s+\$(?P<cost>-?\d+(?:,\d{3})*(?:\.\d{2})?)$",
    re.IGNORECASE,
)
STATUS_PATTERNS = [
    "You're all set! No need to return this item",
    "You\u2019re all set! No need to return this item",
    "Return complete",
    "Weight-adjusted",
    "Shopped",
]
STOP_LINE_PREFIXES = (
    "Invoice",
    "Seller",
    "Buyer",
    "Subtotal",
    "Savings",
    "Tax",
    "Driver tip",
    "Total",
    "Order#",
)


class ParseError(ValueError):
    pass


def parse_invoice_text(raw_text: str, source_path: Path) -> Invoice:
    if not raw_text.strip():
        raise ParseError("PDF did not contain extractable text")

    order_date = _parse_order_date(raw_text)
    items = _parse_items(raw_text)
    if not items:
        raise ParseError("No Walmart item rows found")

    return Invoice(
        source_path=source_path,
        store_name="Walmart",
        order_date=order_date,
        order_number=_parse_order_number(raw_text),
        items=items,
        tax=_parse_money(raw_text, "Tax") or Decimal("0.00"),
        total=_parse_money(raw_text, "Total"),
        raw_text=raw_text,
    )


def _parse_order_date(raw_text: str):
    match = DATE_RE.search(raw_text)
    if not match:
        raise ParseError("Order date not found")

    date_text = match.group(0).replace(" order", "")
    for date_format in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_text, date_format).date()
        except ValueError:
            continue

    raise ParseError(f"Order date format not supported: {date_text}")


def _parse_order_number(raw_text: str) -> str | None:
    match = ORDER_RE.search(raw_text)
    return match.group(1) if match else None


def _parse_money(raw_text: str, label: str) -> Decimal | None:
    match = re.search(MONEY_RE_TEMPLATE.format(label=re.escape(label)), raw_text, re.IGNORECASE)
    if not match:
        return None

    return Decimal(match.group(1).replace(",", ""))


def _parse_items(raw_text: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for line in raw_text.splitlines():
        cleaned_line = " ".join(line.split())
        if not cleaned_line or cleaned_line.startswith(STOP_LINE_PREFIXES):
            continue

        match = ITEM_RE.match(cleaned_line)
        if not match:
            continue

        item_name, status = _split_status(match.group("body").strip())
        items.append(
            InvoiceItem(
                name=item_name,
                cost=Decimal(match.group("cost").replace(",", "")),
                quantity=match.group("qty"),
                status=status,
            )
        )

    return items


def _split_status(body: str) -> tuple[str, str | None]:
    for status in STATUS_PATTERNS:
        status_index = body.rfind(status)
        if status_index == -1:
            continue

        name = body[:status_index].strip(" ,-")
        return name or body, status

    return body, None
