from __future__ import annotations

import argparse
from pathlib import Path
import sys
import traceback

from excel_writer import write_invoices
from models import Invoice, ProcessingResult
from pdf_reader import extract_text
from settings import SettingsError, load_settings
from invoice_parser import parse_invoice_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        settings = load_settings(PROJECT_ROOT / ".env", args.participants, args.output)
    except SettingsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    result = process_invoices(args.input, settings.output_file, settings.participants)
    print_summary(result)
    return 0 if not result.failed_files else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert supported invoice PDFs to an Excel split workbook.")
    parser.add_argument("--input", type=Path, default=Path("input"), help="Folder containing invoice PDFs.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Excel workbook path to create or append to. Overrides OUTPUT_FILE in .env.",
    )
    parser.add_argument(
        "--participants",
        nargs="+",
        default=None,
        help="Participant names. Overrides PARTICIPANTS in .env.",
    )
    return parser.parse_args(argv)


def process_invoices(input_dir: Path, output_path: Path, participants: list[str]) -> ProcessingResult:
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")
    invoices: list[Invoice] = []
    failed_files: list[Path] = []
    debug_dir = output_path.parent / "debug"

    for pdf_path in pdf_paths:
        raw_text = ""
        try:
            raw_text = extract_text(pdf_path)
            invoice = parse_invoice_text(raw_text, pdf_path)
        except Exception as exc:
            failed_files.append(pdf_path)
            _write_debug_text(debug_dir, pdf_path, raw_text, exc)
            continue

        invoices.append(invoice)

    added_sheets = write_invoices(invoices, output_path, participants) if invoices else []
    return ProcessingResult(
        found_pdf_count=len(pdf_paths),
        parsed_count=len(invoices),
        failed_files=failed_files,
        added_sheets=added_sheets,
        output_path=output_path,
    )


def print_summary(result: ProcessingResult) -> None:
    print(f"Found {result.found_pdf_count} PDF files.")
    print(f"Parsed {result.parsed_count} invoices.")
    if result.added_sheets:
        print(f"Workbook: {result.output_path}")
    else:
        print(f"Workbook unchanged: {result.output_path}")
    if result.added_sheets:
        print(f"Added sheets: {', '.join(result.added_sheets)}")
    else:
        print("Added sheets: none")
    print(f"Failed PDFs: {len(result.failed_files)}")
    for failed_file in result.failed_files:
        print(f"- {failed_file}")
    print("Done.")


def _write_debug_text(debug_dir: Path, pdf_path: Path, raw_text: str, error: Exception) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    debug_path = debug_dir / f"{pdf_path.stem}.txt"
    traceback_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    debug_path.write_text(
        f"Error: {error}\n\nTraceback:\n{traceback_text}\n\nExtracted text:\n{raw_text or '[no text extracted]'}",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
