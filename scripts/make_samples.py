"""Writes FICTIONAL sample documents to ./samples for manual testing and the e2e test."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from tests import synth  # noqa: E402

out = root / "samples"
out.mkdir(exist_ok=True)
synth.make_bank_statement_pdf(out / "bank-statement.pdf")
synth.pdf_to_scanned(out / "bank-statement.pdf", out / "bank-statement-scanned.pdf")
synth.make_invoice_pdf(out / "invoice.pdf")
synth.make_receipt_pdf(out / "receipt.pdf")
synth.pdf_page_to_png(out / "receipt.pdf", out / "receipt.png", dpi=300)
synth.make_table_pdf(out / "table.pdf")
print("Wrote", sorted(p.name for p in out.iterdir()))
