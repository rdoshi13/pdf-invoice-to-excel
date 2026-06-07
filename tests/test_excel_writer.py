from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

from src.excel_writer import write_invoices
from src.models import Invoice, InvoiceItem


def make_invoice(order_date: date, source: str = "invoice.pdf") -> Invoice:
    return Invoice(
        source_path=Path(source),
        order_date=order_date,
        order_number="123",
        items=[
            InvoiceItem("Apple", Decimal("2.71")),
            InvoiceItem("Normal Bananas", Decimal("1.42")),
        ],
        tax=Decimal("0.71"),
        total=Decimal("4.84"),
        raw_text="raw",
    )


def test_write_invoice_sheet_layout_and_formulas(tmp_path):
    output_path = tmp_path / "walmart_orders.xlsx"

    added = write_invoices([make_invoice(date(2024, 5, 1))], output_path)

    workbook = load_workbook(output_path, data_only=False)
    worksheet = workbook[added[0]]

    assert added == ["1 May 2024"]
    assert worksheet["A1"].value == "Walmart 1 May 2024"
    assert "A1:N1" in [str(cell_range) for cell_range in worksheet.merged_cells.ranges]
    assert [worksheet.cell(row=2, column=column).value for column in range(1, 15)] == [
        "Items",
        "Cost",
        "Rakshit",
        "Ansh",
        "Rishabh",
        "Varun",
        "Anuj",
        "Involved",
        "Per Person",
        "Rakshit",
        "Ansh",
        "Rishabh",
        "Varun",
        "Anuj",
    ]
    assert worksheet["A5"].value == "Walmart Tax"
    assert worksheet["H3"].value == "=SUM(C3:G3)"
    assert worksheet["I3"].value == "=IF(H3=0,0,B3/H3)"
    assert worksheet["J3"].value == "=IF(C3=1,I3,0)"
    assert worksheet["N3"].value == "=IF(G3=1,I3,0)"
    assert worksheet["A6"].value == "Total"
    assert worksheet["B6"].value == "=SUM(B3:B5)"
    assert worksheet["J6"].value == "=SUM(J3:J5)"
    assert worksheet.freeze_panes == "A3"


def test_write_invoice_sheet_anuj_excluded_after_november_8(tmp_path):
    output_path = tmp_path / "walmart_orders.xlsx"

    added = write_invoices([make_invoice(date(2024, 11, 8))], output_path)

    worksheet = load_workbook(output_path, data_only=False)[added[0]]
    assert worksheet["G3"].value is None
    assert worksheet["N3"].value == "=0"
    assert worksheet["N6"].value == "=SUM(N3:N5)"


def test_duplicate_sheet_names_append_safely(tmp_path):
    output_path = tmp_path / "walmart_orders.xlsx"

    first = write_invoices([make_invoice(date(2024, 6, 16))], output_path)
    second = write_invoices([make_invoice(date(2024, 6, 16), "other.pdf")], output_path)

    assert first == ["16 June 2024"]
    assert second == ["16 June 2024 2"]
    workbook = load_workbook(output_path)
    assert "16 June 2024" in workbook.sheetnames
    assert "16 June 2024 2" in workbook.sheetnames


def test_worksheets_are_sorted_by_date(tmp_path):
    output_path = tmp_path / "walmart_orders.xlsx"

    added = write_invoices(
        [
            make_invoice(date(2024, 8, 18)),
            make_invoice(date(2024, 5, 12)),
            make_invoice(date(2025, 2, 18)),
            make_invoice(date(2024, 4, 20)),
        ],
        output_path,
    )

    assert added == ["20 April 2024", "12 May 2024", "18 August 2024", "18 February 2025"]
    workbook = load_workbook(output_path)
    assert workbook.sheetnames == ["20 April 2024", "12 May 2024", "18 August 2024", "18 February 2025"]
