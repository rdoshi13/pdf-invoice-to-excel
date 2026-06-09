from datetime import date
from decimal import Decimal
from pathlib import Path

from src import main
from src.models import Invoice, InvoiceItem


def test_cli_processes_multiple_pdfs_with_mocked_extraction(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "b.pdf").write_text("pdf", encoding="utf-8")
    (input_dir / "a.pdf").write_text("pdf", encoding="utf-8")
    (input_dir / "notes.txt").write_text("skip", encoding="utf-8")
    output_path = tmp_path / "output" / "walmart_orders.xlsx"

    def fake_extract_text(pdf_path: Path) -> str:
        return f"raw {pdf_path.name}"

    def fake_parse_invoice_text(raw_text: str, source_path: Path) -> Invoice:
        day = 1 if source_path.name == "a.pdf" else 2
        return Invoice(
            source_path=source_path,
            store_name="Walmart",
            order_date=date(2024, 5, day),
            order_number=source_path.stem,
            items=[InvoiceItem("Apple", Decimal("2.00"))],
            tax=Decimal("0.10"),
            total=Decimal("2.10"),
            raw_text=raw_text,
        )

    captured: dict[str, object] = {}

    def fake_write_invoices(invoices: list[Invoice], output: Path, participants: list[str]) -> list[str]:
        captured["invoices"] = invoices
        captured["output"] = output
        captured["participants"] = participants
        return [f"{invoice.order_date.day} May 2024" for invoice in invoices]

    monkeypatch.setattr(main, "extract_text", fake_extract_text)
    monkeypatch.setattr(main, "parse_invoice_text", fake_parse_invoice_text)
    monkeypatch.setattr(main, "write_invoices", fake_write_invoices)

    result = main.process_invoices(input_dir, output_path, ["Alice", "Bob"])

    assert result.found_pdf_count == 2
    assert result.parsed_count == 2
    assert result.failed_files == []
    assert result.added_sheets == ["1 May 2024", "2 May 2024"]
    assert captured["output"] == output_path
    assert captured["participants"] == ["Alice", "Bob"]


def test_main_uses_cli_overrides(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    output_path = tmp_path / "custom.xlsx"
    captured: dict[str, object] = {}

    def fake_process_invoices(input_path: Path, output: Path, participants: list[str]):
        captured["input"] = input_path
        captured["output"] = output
        captured["participants"] = participants
        return main.ProcessingResult(
            found_pdf_count=0,
            parsed_count=0,
            failed_files=[],
            added_sheets=[],
            output_path=output,
        )

    monkeypatch.setattr(main, "process_invoices", fake_process_invoices)

    exit_code = main.main(
        [
            "--input",
            str(input_dir),
            "--output",
            str(output_path),
            "--participants",
            "Alice",
            "Bob",
        ]
    )

    assert exit_code == 0
    assert captured["input"] == input_dir
    assert captured["output"] == output_path
    assert captured["participants"] == ["Alice", "Bob"]


def test_process_invoices_writes_debug_when_extraction_fails(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    pdf_path = input_dir / "scan.pdf"
    pdf_path.write_text("pdf", encoding="utf-8")
    output_path = tmp_path / "output" / "walmart_orders.xlsx"

    def fake_extract_text(source_path: Path) -> str:
        raise RuntimeError("Extraction failed")

    monkeypatch.setattr(main, "extract_text", fake_extract_text)

    result = main.process_invoices(input_dir, output_path, ["Alice"])

    debug_file = tmp_path / "output" / "debug" / "scan.txt"
    assert result.failed_files == [pdf_path]
    assert debug_file.exists()
    debug_text = debug_file.read_text(encoding="utf-8")
    assert "Extraction failed" in debug_text
    assert "[no text extracted]" in debug_text
