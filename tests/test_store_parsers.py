from decimal import Decimal
from pathlib import Path

from src.amazon_parser import parse_invoice_text as parse_amazon_invoice
from src.costco_parser import parse_invoice_text as parse_costco_invoice
from src.invoice_parser import parse_invoice_text
from src.target_parser import parse_invoice_text as parse_target_invoice


AMAZON_TEXT = """Amazon.com
Invoice date: October 18, 2018
Order # 111-2222222-3333333
Invoice details
Description Qty Unit price Item subtotal
1 $49.99 $49.99 6.000%
1
Echo Dot smart speaker
ASIN: B07FZ8S74R
2 USB-C Cable, 6 ft 2 $7.50 $15.00
Tax $3.25
Amount due $ 68.24
"""


AMAZON_ORDER_SUMMARY_TEXT = """08/06/2026, 17:51 Order Details
Order Summary
Order placed August 26, 2024 Order # 114-6978098-1633837
Ship to Payment method Order Summary
Rishabh Doshi Visa ending in 1301 Item(s) Subtotal: $52.64
1275 E University Dr View related transactions Shipping & Handling: $0.00
211 Total before tax: $52.64
Tempe, AZ 85281 Estimated tax to be $4.26
United States collected:
Grand Total: $56.90
Hawkins/Futura Nonstick Tava/Griddle, 0, Gray
Sold by: Nutrition Bizz
$39.90
Nautica Voyage Eau De Toilette for Men - Fresh, Romantic, Fruity Scent Woody,
Aquatic Notes of Apple, Water Lotus, Cedarwood, and Musk Ideal Day Wear 3.3 Fl
Oz
Sold by: Amazon.com
Supplied by: Other
$12.74
Back to top
"""


TARGET_TEXT = """Target
Order date: May 12, 2025
Order number: 9050500000000
Good & Gather Grade A Large Eggs Qty 2 $5.98
Market Pantry Pasta Sauce Quantity 1 $2.49
Subtotal $8.47
Tax $0.57
Order total $9.04
"""


COSTCO_TEXT = """Costco
Order Date: 04/20/2024
Order Number: 123456789
Item Quantity Price Total
Kirkland Signature Organic Eggs 2 $6.99 $13.98
Organic Bananas Qty 1 $2.49
Subtotal $16.47
Sales tax $1.32
Order total $17.79
"""


def test_parse_amazon_invoice_table_rows():
    invoice = parse_amazon_invoice(AMAZON_TEXT, Path("amazon.pdf"))

    assert invoice.store_name == "Amazon"
    assert invoice.order_date.isoformat() == "2018-10-18"
    assert invoice.order_number == "111-2222222-3333333"
    assert [(item.name, item.quantity, item.cost) for item in invoice.items] == [
        ("Echo Dot smart speaker", "1", Decimal("49.99")),
        ("USB-C Cable, 6 ft", "2", Decimal("15.00")),
    ]
    assert invoice.tax == Decimal("3.25")
    assert invoice.total == Decimal("68.24")


def test_parse_amazon_order_summary_rows():
    invoice = parse_amazon_invoice(AMAZON_ORDER_SUMMARY_TEXT, Path("amazon-summary.pdf"))

    assert invoice.order_date.isoformat() == "2024-08-26"
    assert invoice.order_number == "114-6978098-1633837"
    assert [(item.name, item.quantity, item.cost) for item in invoice.items] == [
        ("Hawkins/Futura Nonstick Tava/Griddle, 0, Gray", "1", Decimal("39.90")),
        (
            "Nautica Voyage Eau De Toilette for Men - Fresh, Romantic, Fruity Scent Woody, "
            "Aquatic Notes of Apple, Water Lotus, Cedarwood, and Musk Ideal Day Wear 3.3 Fl Oz",
            "1",
            Decimal("12.74"),
        ),
    ]
    assert invoice.tax == Decimal("4.26")
    assert invoice.total == Decimal("56.90")


def test_parse_target_invoice_qty_rows():
    invoice = parse_target_invoice(TARGET_TEXT, Path("target.pdf"))

    assert invoice.store_name == "Target"
    assert invoice.order_date.isoformat() == "2025-05-12"
    assert invoice.order_number == "9050500000000"
    assert [(item.name, item.quantity, item.cost) for item in invoice.items] == [
        ("Good & Gather Grade A Large Eggs", "2", Decimal("5.98")),
        ("Market Pantry Pasta Sauce", "1", Decimal("2.49")),
    ]
    assert invoice.tax == Decimal("0.57")
    assert invoice.total == Decimal("9.04")


def test_parse_costco_invoice_total_rows():
    invoice = parse_costco_invoice(COSTCO_TEXT, Path("costco.pdf"))

    assert invoice.store_name == "Costco"
    assert invoice.order_date.isoformat() == "2024-04-20"
    assert invoice.order_number == "123456789"
    assert [(item.name, item.quantity, item.cost) for item in invoice.items] == [
        ("Kirkland Signature Organic Eggs", "2", Decimal("13.98")),
        ("Organic Bananas", "1", Decimal("2.49")),
    ]
    assert invoice.tax == Decimal("1.32")
    assert invoice.total == Decimal("17.79")


def test_parser_registry_detects_supported_stores():
    assert parse_invoice_text(AMAZON_TEXT, Path("amazon.pdf")).store_name == "Amazon"
    assert parse_invoice_text(TARGET_TEXT, Path("target.pdf")).store_name == "Target"
    assert parse_invoice_text(COSTCO_TEXT, Path("costco.pdf")).store_name == "Costco"
