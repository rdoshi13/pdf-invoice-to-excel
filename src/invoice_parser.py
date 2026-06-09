from __future__ import annotations

from pathlib import Path

import amazon_parser
import costco_parser
import target_parser
import walmart_parser
from models import Invoice
from walmart_parser import ParseError


PARSERS = (
    walmart_parser.parse_invoice_text,
    amazon_parser.parse_invoice_text,
    costco_parser.parse_invoice_text,
    target_parser.parse_invoice_text,
)


def parse_invoice_text(raw_text: str, source_path: Path) -> Invoice:
    errors: list[str] = []
    for parser in PARSERS:
        try:
            return parser(raw_text, source_path)
        except ParseError as exc:
            errors.append(str(exc))

    raise ParseError("No supported invoice parser matched. Tried Walmart, Amazon, Costco, and Target. " + " | ".join(errors))
