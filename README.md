# pdf-invoice-to-excel

A local Python command-line tool that converts Walmart invoice PDFs into an Excel workbook for grocery cost splitting.

Add your participant names once in a local `.env` file, drop Walmart order/invoice PDFs into `input/`, run one command, and the app creates a workbook where each invoice becomes its own worksheet. The generated sheets include item quantities, item costs, editable participant flags, per-person formulas, and final totals.

## How To Use

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create your local `.env` file:

```bash
cp .env.example .env
```

3. Edit `.env` and add your names:

```text
PARTICIPANTS=Alice,Bob,Charlie
OUTPUT_FILE=output/walmart_orders.xlsx
```

4. Put your Walmart invoice PDFs into the `input/` folder.
5. Run:

```bash
python src.main.py
```

The app automatically reads from `input/` and writes to `output/walmart_orders.xlsx` unless `OUTPUT_FILE` is changed in `.env`.

## What It Does

- Reads every `.pdf` file from an input folder.
- Extracts text from Walmart invoice/order PDFs.
- Falls back to local OCR for scanned PDFs when normal PDF text extraction is empty or too short.
- Parses order date, order number, item names, quantities, item costs, tax, and total.
- Creates or updates a single `.xlsx` workbook.
- Adds one worksheet per invoice, named by order date, such as `1 March 2024` or `16 June 2025`.
- Sorts worksheets in ascending order by invoice date.
- Keeps duplicate sheet names safe by appending a number, such as `16 June 2025 2`.
- Creates participant columns from the names in `.env`.
- Adds formulas so the split totals update automatically when participant flags are edited.

## Requirements

- Python 3.11 or newer recommended
- `pdfplumber`
- `pytesseract`
- `pdf2image`
- `pillow`
- `openpyxl`
- `pytest` for running tests

For OCR fallback, install the native Tesseract and Poppler tools too.

macOS:

```bash
brew install tesseract poppler
```

Windows PowerShell:

```powershell
winget install UB-Mannheim.TesseractOCR
winget install oschwartz10612.Poppler
```

After installing on Windows, close and reopen PowerShell so `PATH` refreshes, then verify:

```powershell
tesseract --version
pdftoppm -v
```

If `pdftoppm` is not found, add Poppler's `bin` folder to your Windows `PATH`.

## Advanced Usage

The simple command above is usually enough. To choose custom folders, a custom workbook path, or one-off participant names, use:

```bash
python src/main.py --input input --output output/custom.xlsx --participants Alice Bob Charlie
```

CLI values override `.env` values for that run.

Open the generated workbook in Excel, Apple Numbers, or Google Sheets. In each worksheet, enter `1` or `0` in the participant flag columns to mark who shared each item.

Example output:

```text
Found 6 PDF files.
Parsed 6 invoices.
Workbook: output/walmart_orders.xlsx
Added sheets: 1 March 2024, 31 March 2024, 1 May 2024, 16 May 2024, 25 May 2024, 16 June 2024
Failed PDFs: 0
Done.
```

## Workbook Layout

Each invoice gets one worksheet.

Rows:

```text
Row 1: merged title row, e.g. Walmart 25 May 2024
Row 2: column headers
Row 3+: invoice item rows
Final row: Total
```

Columns are generated dynamically from your participant names:

```text
A: Items
B: Qty
C: Cost
D onward: participant flag columns
Next: Involved
Next: Per Person
Remaining columns: participant owed amount columns
```

For example, with:

```text
PARTICIPANTS=Alice,Bob,Charlie
```

the headers are:

```text
Items | Qty | Cost | Alice | Bob | Charlie | Involved | Per Person | Alice | Bob | Charlie
```

The app also adds `Walmart Tax` as a split-able row when tax is present in the invoice.

Generated formulas follow this pattern:

```text
Involved   = SUM(participant flag cells)
Per Person = IF(Involved=0,0,Cost/Involved)
Owed       = IF(participant flag=1,Per Person,0)
```

The final row sums total item cost and each participant's owed amount.

## Supported Input

The parser expects Walmart invoice text similar to:

```text
Invoice
May 12, 2026 order
Order# 2000147-51516982
Fresh Roma Tomato, Each Weight-adjusted Qty 12 $6.20
Coca-Cola Zero Sugar Soda Pop Bottle, 2 Liters Shopped Qty 2 $5.94
Tax $0.93
Total $37.49
```

Known item statuses include:

- `Weight-adjusted`
- `Shopped`
- `Return complete`
- `You're all set! No need to return this item`

If a PDF has little or no embedded text, the app falls back to local Tesseract OCR and then sends the OCR text through the same Walmart parser. If a PDF still cannot be parsed, the app skips it, continues processing the rest, and writes debug text under `output/debug/` when extracted text is available.

## Running Tests

```bash
pytest
```

The tests cover `.env` settings, Walmart parsing, workbook formulas/layout, duplicate sheet names, date sorting, and CLI orchestration.

## Project Structure

```text
src/
  main.py           CLI entrypoint and orchestration
  settings.py       Local .env settings loader
  models.py         Shared dataclasses
  pdf_reader.py     PDF text extraction
  walmart_parser.py Walmart invoice parser
  excel_writer.py   Workbook generation
tests/
  test_*.py
```

## Limitations

- Walmart invoices only.
- No web UI.
- No Google Sheets API integration.
- No cloud upload.
- No AI/LLM parsing.

## Future Ideas

- Add support for more stores.
- Add a summary sheet across all orders.
- Detect duplicate PDFs by order number.
- Add monthly spending summaries.
- Add Google Sheets export.
