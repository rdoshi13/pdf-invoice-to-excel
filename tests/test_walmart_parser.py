from decimal import Decimal
from pathlib import Path

from src.walmart_parser import parse_invoice_text


SAMPLE_TEXT = """Invoice
May 12, 2026 order
Order# 2000147-51516982
Seller
MY BATTERY SUPPLIER
Buyer
RAKSHIT VASAVA
Fresh Roma Tomato, Each Weight-adjusted Qty 12 $6.20
Coca-Cola Zero Sugar Soda Pop Bottle, 2 Liters Shopped Qty 2 $5.94
Lay's Wavy Potato Chips, Original Flavor, 7.75 oz Bag Return complete Qty 1 $4.00
Great Value Grade AA Extra Large Eggs,18 Count You're all set! No need to return this item Qty 1 $2.43
Energizer Alkaline Battery, Size: AA - Pack of 2 Qty 1 $6.51
Subtotal $40.33
Savings -$3.77
Tax $0.93
Driver tip $0.00
Total $37.49
"""


def test_parse_invoice_order_fields():
    invoice = parse_invoice_text(SAMPLE_TEXT, Path("invoice.pdf"))

    assert invoice.order_date.isoformat() == "2026-05-12"
    assert invoice.order_number == "2000147-51516982"
    assert invoice.tax == Decimal("0.93")
    assert invoice.total == Decimal("37.49")


def test_parse_invoice_items_and_statuses():
    invoice = parse_invoice_text(SAMPLE_TEXT, Path("invoice.pdf"))

    assert [item.name for item in invoice.items] == [
        "Fresh Roma Tomato, Each",
        "Coca-Cola Zero Sugar Soda Pop Bottle, 2 Liters",
        "Lay's Wavy Potato Chips, Original Flavor, 7.75 oz Bag",
        "Great Value Grade AA Extra Large Eggs,18 Count",
        "Energizer Alkaline Battery, Size: AA - Pack of 2",
    ]
    assert [item.status for item in invoice.items] == [
        "Weight-adjusted",
        "Shopped",
        "Return complete",
        "You're all set! No need to return this item",
        None,
    ]
    assert [item.quantity for item in invoice.items] == ["12", "2", "1", "1", "1"]
    assert invoice.items[-1].cost == Decimal("6.51")


def test_missing_optional_total_is_none():
    text = SAMPLE_TEXT.replace("Total $37.49\n", "")

    invoice = parse_invoice_text(text, Path("invoice.pdf"))

    assert invoice.total is None
