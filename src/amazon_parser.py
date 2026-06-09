from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re

from models import Invoice, InvoiceItem
from parser_utils import compact_line, find_money, parse_date_text, parse_decimal
from walmart_parser import ParseError


DATE_PATTERNS = [
    re.compile(r"\bInvoice\s+date\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
    re.compile(r"\bPurchase\s+date\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
    re.compile(r"\bOrder\s+placed\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE),
]
ORDER_RE = re.compile(r"\bOrder\s*#\s*:?\s*([A-Za-z0-9-]+)", re.IGNORECASE)
ITEM_TOTAL_RE = re.compile(
    r"^(?P<qty>\d+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<unit>-?\d+(?:,\d{3})*(?:\.\d{2})?)\s+"
    r"\$?\s*(?P<cost>-?\d+(?:,\d{3})*(?:\.\d{2})?)"
    r"(?:\s+\d+(?:\.\d+)?%)?"
    r"(?:\s+\$?\s*-?\d+(?:,\d{3})*(?:\.\d{2})?){0,2}$"
)
INLINE_ITEM_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+"
    r"\$?(?P<unit>-?\d+(?:,\d{3})*(?:\.\d{2})?)\s+"
    r"\$?(?P<cost>-?\d+(?:,\d{3})*(?:\.\d{2})?)$"
)
SKIP_PREFIXES = (
    "Amazon",
    "Invoice",
    "Order #",
    "Order#",
    "ASIN",
    "Sold by",
    "Billing address",
    "Shipping address",
    "Payment",
    "Description",
    "Subtotal",
    "Tax",
    "Total",
    "Amount due",
)


def parse_invoice_text(raw_text: str, source_path: Path) -> Invoice:
    if "amazon" not in raw_text.lower():
        raise ParseError("Not an Amazon invoice")

    order_date = _parse_order_date(raw_text)
    items = _parse_items(raw_text)
    if not items:
        raise ParseError("No Amazon item rows found")

    return Invoice(
        source_path=source_path,
        store_name="Amazon",
        order_date=order_date,
        order_number=_parse_order_number(raw_text),
        items=items,
        tax=find_money(raw_text, ("Estimated tax to be", "Sales tax", "Tax")) or Decimal("0.00"),
        total=find_money(raw_text, ("Grand Total", "Total", "Amount due")),
        raw_text=raw_text,
    )


def _parse_order_date(raw_text: str):
    for pattern in DATE_PATTERNS:
        match = pattern.search(raw_text)
        if match:
            return parse_date_text(match.group(1), ("%B %d, %Y", "%b %d, %Y"))

    raise ParseError("Amazon order date not found")


def _parse_order_number(raw_text: str) -> str | None:
    match = ORDER_RE.search(raw_text)
    return match.group(1) if match else None


def _parse_items(raw_text: str) -> list[InvoiceItem]:
    summary_items = _parse_order_summary_items(raw_text)
    if summary_items:
        return summary_items

    items: list[InvoiceItem] = []
    pending_name: str | None = None
    pending_price: tuple[str, Decimal] | None = None

    for raw_line in raw_text.splitlines():
        line = compact_line(raw_line)
        if not line:
            continue

        inline_match = INLINE_ITEM_RE.match(line)
        if inline_match and not line.startswith(SKIP_PREFIXES):
            items.append(_item_from_match(inline_match))
            pending_name = None
            continue

        if line.startswith(SKIP_PREFIXES) or line in {"Qty", "Unit price"}:
            continue

        total_match = ITEM_TOTAL_RE.match(line)
        if total_match and pending_name:
            items.append(
                InvoiceItem(
                    name=pending_name,
                    quantity=total_match.group("qty"),
                    cost=parse_decimal(total_match.group("cost")),
                )
            )
            pending_name = None
            continue
        if total_match:
            pending_price = (total_match.group("qty"), parse_decimal(total_match.group("cost")))
            continue

        if re.fullmatch(r"\d+", line):
            continue

        numbered_match = re.match(r"^\d+\s+(.+)$", line)
        item_name = numbered_match.group(1) if numbered_match else line
        if pending_price:
            quantity, cost = pending_price
            items.append(InvoiceItem(name=item_name, quantity=quantity, cost=cost))
            pending_price = None
            continue

        pending_name = item_name

    return items


def _parse_order_summary_items(raw_text: str) -> list[InvoiceItem]:
    lines = [compact_line(line) for line in raw_text.splitlines()]
    items: list[InvoiceItem] = []
    name_parts: list[str] = []
    collecting_items = False
    waiting_for_price = False

    for line in lines:
        if not line:
            continue
        if line.startswith("Grand Total"):
            collecting_items = True
            continue
        if not collecting_items:
            continue
        if line.startswith(("Back to top", "Conditions of Use", "©", "https://")):
            break
        if line.startswith(("Sold by:", "Supplied by:")):
            waiting_for_price = True
            continue
        if waiting_for_price and re.fullmatch(r"\$?\s*-?\d+(?:,\d{3})*(?:\.\d{2})", line):
            item_name = " ".join(name_parts).strip()
            if item_name:
                items.append(InvoiceItem(name=item_name, quantity="1", cost=parse_decimal(line)))
            name_parts = []
            waiting_for_price = False
            continue
        if waiting_for_price:
            continue

        name_parts.append(line)

    return items


def _item_from_match(match: re.Match[str]) -> InvoiceItem:
    name = re.sub(r"^\d+\s+", "", match.group("name").strip())
    return InvoiceItem(
        name=name,
        quantity=match.group("qty"),
        cost=parse_decimal(match.group("cost")),
    )
