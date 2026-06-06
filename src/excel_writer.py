from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from models import Invoice, InvoiceItem
from participant_rules import ALL_PARTICIPANTS, ANUJ, is_anuj_excluded


HEADERS = [
    "Items",
    "Cost",
    *ALL_PARTICIPANTS,
    "Involved",
    "Per Person",
    *ALL_PARTICIPANTS,
]
FLAG_COLUMNS = ["C", "D", "E", "F", "G"]
OWED_COLUMNS = ["J", "K", "L", "M", "N"]
GREEN_FILL = PatternFill("solid", fgColor="D9EAD3")
HEADER_FILL = PatternFill("solid", fgColor="D9EAD3")
CURRENCY_FORMAT = "0.00"
INVALID_SHEET_CHARS = re.compile(r"[:\\/?*\[\]]")


def write_invoices(invoices: list[Invoice], output_path: Path) -> list[str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(output_path) if output_path.exists() else Workbook()

    if workbook.sheetnames == ["Sheet"] and not workbook["Sheet"].max_row > 1:
        workbook.remove(workbook["Sheet"])

    added_sheets: list[str] = []
    for invoice in invoices:
        sheet_name = unique_sheet_name(workbook.sheetnames, date_sheet_name(invoice.order_date))
        worksheet = workbook.create_sheet(sheet_name)
        write_invoice_sheet(worksheet, invoice)
        added_sheets.append(sheet_name)

    workbook.save(output_path)
    return added_sheets


def write_invoice_sheet(worksheet: Worksheet, invoice: Invoice) -> None:
    title = f"Walmart {date_sheet_name(invoice.order_date)}"
    rows = list(invoice.items)
    if invoice.tax != Decimal("0"):
        rows.append(InvoiceItem(name="Walmart Tax", cost=invoice.tax))

    _write_title(worksheet, title)
    _write_headers(worksheet)
    _write_item_rows(worksheet, rows, invoice.order_date)
    _write_total_row(worksheet, len(rows))
    _format_sheet(worksheet, len(rows))


def date_sheet_name(order_date: date) -> str:
    return f"{order_date.day} {order_date.strftime('%B')}"


def unique_sheet_name(existing_names: list[str], desired_name: str) -> str:
    base = sanitize_sheet_name(desired_name)
    if base not in existing_names:
        return base

    counter = 2
    while True:
        suffix = f" {counter}"
        candidate = sanitize_sheet_name(f"{base[:31 - len(suffix)]}{suffix}")
        if candidate not in existing_names:
            return candidate
        counter += 1


def sanitize_sheet_name(name: str) -> str:
    sanitized = INVALID_SHEET_CHARS.sub(" ", name).strip() or "Sheet"
    return sanitized[:31]


def _write_title(worksheet: Worksheet, title: str) -> None:
    worksheet.merge_cells("A1:N1")
    cell = worksheet["A1"]
    cell.value = title
    cell.fill = GREEN_FILL
    cell.font = Font(size=22)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    worksheet.row_dimensions[1].height = 34


def _write_headers(worksheet: Worksheet) -> None:
    for column_index, header in enumerate(HEADERS, start=1):
        cell = worksheet.cell(row=2, column=column_index, value=header)
        cell.fill = HEADER_FILL
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _write_item_rows(worksheet: Worksheet, rows: list[InvoiceItem], order_date: date) -> None:
    anuj_excluded = is_anuj_excluded(order_date)
    for row_offset, item in enumerate(rows, start=3):
        worksheet.cell(row=row_offset, column=1, value=item.name)
        worksheet.cell(row=row_offset, column=2, value=float(item.cost))

        if anuj_excluded:
            worksheet.cell(row=row_offset, column=14, value=0)

        worksheet.cell(row=row_offset, column=8, value=f"=SUM(C{row_offset}:G{row_offset})")
        worksheet.cell(row=row_offset, column=9, value=f"=IF(H{row_offset}=0,0,B{row_offset}/H{row_offset})")

        for flag_column, owed_column in zip(FLAG_COLUMNS, OWED_COLUMNS, strict=True):
            if owed_column == "N" and anuj_excluded:
                formula = "=0"
            else:
                formula = f"=IF({flag_column}{row_offset}=1,I{row_offset},0)"
            worksheet[f"{owed_column}{row_offset}"] = formula


def _write_total_row(worksheet: Worksheet, item_count: int) -> None:
    total_row = item_count + 3
    last_item_row = total_row - 1
    worksheet.cell(row=total_row, column=1, value="Total")
    worksheet.cell(row=total_row, column=2, value=f"=SUM(B3:B{last_item_row})")

    for owed_column in OWED_COLUMNS:
        worksheet[f"{owed_column}{total_row}"] = f"=SUM({owed_column}3:{owed_column}{last_item_row})"

    for column in range(1, 15):
        worksheet.cell(row=total_row, column=column).font = Font(bold=True)


def _format_sheet(worksheet: Worksheet, item_count: int) -> None:
    worksheet.freeze_panes = "A3"

    widths = {
        "A": 28,
        "B": 12,
        "C": 12,
        "D": 12,
        "E": 12,
        "F": 12,
        "G": 12,
        "H": 12,
        "I": 12,
        "J": 12,
        "K": 12,
        "L": 12,
        "M": 12,
        "N": 12,
    }
    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width

    final_row = item_count + 3
    for row in range(3, final_row + 1):
        for column in (2, 9, 10, 11, 12, 13, 14):
            worksheet.cell(row=row, column=column).number_format = CURRENCY_FORMAT
        for column in range(2, 15):
            worksheet.cell(row=row, column=column).alignment = Alignment(horizontal="right")

    for column_index in range(1, 15):
        column_letter = get_column_letter(column_index)
        worksheet[f"{column_letter}1"].fill = GREEN_FILL
