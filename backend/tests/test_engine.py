"""Engine tests on synthetic, fictional documents (no FastAPI needed).

Run:  python -m unittest discover -s tests -v      (pytest also works)
"""
from __future__ import annotations

import csv
import dataclasses
import io
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpyxl import load_workbook  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.errors import AppError, ExtractionError  # noqa: E402
from app.core.jobs import JobStore  # noqa: E402
from app.services import bank_statement_service as bank  # noqa: E402
from app.services import export_service as ex  # noqa: E402
from app.services import invoice_service, ocr_service, receipt_service, table_service  # noqa: E402
from app.services.document_service import read_document  # noqa: E402
from app.services.file_validation_service import sniff, validate_upload  # noqa: E402
from app.services.pipeline import run_job  # noqa: E402
from app.services.result_service import apply_patch  # noqa: E402
from app.utils.dates import parse_date  # noqa: E402
from tests import synth  # noqa: E402

OCR = ocr_service.ocr_available(get_settings())


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.settings = dataclasses.replace(get_settings(), jobs_dir=cls.tmp / "jobs", max_upload_mb=1, max_pdf_pages=5)
        cls.bank_pdf = cls.tmp / "bank.pdf"
        synth.make_bank_statement_pdf(cls.bank_pdf)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def bank_result(self, path=None):
        return bank.extract_bank_statement(read_document(path or self.bank_pdf, "pdf", self.settings))


class TestValidation(Base):
    def test_accepts_real_pdf_and_sanitises_name(self):
        v = validate_upload("../../evil name?.pdf", self.bank_pdf.read_bytes(), "bank_statement", self.settings)
        self.assertEqual(v.kind, "pdf")
        self.assertNotIn("/", v.safe_name)
        self.assertNotIn("..", v.safe_name.replace("_", ""))

    def test_rejects_wrong_signature_even_with_pdf_name(self):
        with self.assertRaises(AppError) as c:
            validate_upload("statement.pdf", b"MZ\x90\x00 not a pdf", "bank_statement", self.settings)
        self.assertEqual(c.exception.code, "unsupported_type")

    def test_rejects_image_for_bank_statement_tool(self):
        png = self.tmp / "x.png"
        synth.pdf_page_to_png(self.bank_pdf, png, dpi=100)
        with self.assertRaises(AppError):
            validate_upload("x.png", png.read_bytes(), "bank_statement", self.settings)
        self.assertEqual(validate_upload("x.png", png.read_bytes(), "invoice", self.settings).kind, "png")

    def test_oversized_and_empty(self):
        with self.assertRaises(AppError) as c:
            validate_upload("a.pdf", b"%PDF-" + b"0" * (2 * 1024 * 1024), "tables", self.settings)
        self.assertEqual(c.exception.code, "file_too_large")
        with self.assertRaises(AppError) as c:
            validate_upload("a.pdf", b"", "tables", self.settings)
        self.assertEqual(c.exception.code, "empty_file")

    def test_corrupt_image_and_sniffing(self):
        with self.assertRaises(AppError) as c:
            validate_upload("a.png", b"\x89PNG\r\n\x1a\n" + b"garbage" * 10, "receipt", self.settings)
        self.assertEqual(c.exception.code, "image_corrupt")
        self.assertEqual(sniff(b"RIFF\x00\x00\x00\x00WEBPVP8 "), "webp")
        self.assertEqual(sniff(b"\xff\xd8\xff\xe0"), "jpeg")


class TestBankText(Base):
    def test_digital_statement_end_to_end(self):
        r = self.bank_result()
        tx = r["transactions"]
        self.assertEqual(len(tx), 6)
        self.assertEqual([t["date"] for t in tx][:2], ["2025-04-01", "2025-04-02"])
        self.assertEqual(tx[0]["debit"], 450.0)
        self.assertIsNone(tx[0]["credit"])
        self.assertEqual(tx[1]["credit"], 50000.0)
        self.assertEqual(tx[3]["balance"], 45049.5)  # first row on page 2
        self.assertEqual(tx[2]["cheque_no"], "123456")
        self.assertIn("SALARY APRIL", tx[1]["description"])  # wrapped narration kept
        self.assertEqual(r["metadata"]["opening_balance"], 10000.0)
        self.assertEqual(r["metadata"]["account_number_masked"], "XXXXXXXX1234")
        self.assertEqual(r["metadata"]["period_to"], "2025-04-30")
        self.assertEqual(r["summary"]["total_debit"], 16184.5)
        self.assertEqual(r["summary"]["computed_closing_balance"], r["summary"]["closing_balance"])
        self.assertEqual(r["warnings"], [])
        self.assertTrue(all(not t["flags"] for t in tx))
        self.assertFalse(r["extraction"]["ocr_used"])

    def test_full_account_number_never_in_result(self):
        self.assertNotIn("555500001234", str(self.bank_result()))

    def test_date_normalisation(self):
        self.assertEqual(parse_date("05/04/2025").isoformat(), "2025-04-05")
        self.assertEqual(parse_date("5-Apr-25").isoformat(), "2025-04-05")
        self.assertEqual(parse_date("05 April 2025").isoformat(), "2025-04-05")
        self.assertEqual(parse_date("2025-04-05").isoformat(), "2025-04-05")
        self.assertIsNone(parse_date("31/02/2025"))

    def test_validation_flags_mismatch_and_duplicates(self):
        rows = [
            {"id": "a", "date": "2025-04-01", "description": "X", "debit": 100.0, "credit": None, "balance": 900.0, "flags": []},
            {"id": "b", "date": "2025-04-01", "description": "X", "debit": 100.0, "credit": None, "balance": 700.0, "flags": []},
            {"id": "c", "date": "bad", "description": "Y", "debit": None, "credit": None, "balance": None, "flags": []},
        ]
        rows, warnings, summary = bank.validate_transactions(rows, {"opening_balance": 1000.0, "closing_balance": 500.0})
        self.assertIn("possible_duplicate", rows[0]["flags"])
        self.assertIn("balance_mismatch", rows[1]["flags"])
        self.assertIn("invalid_date", rows[2]["flags"])
        self.assertIn("missing_amount", rows[2]["flags"])
        self.assertTrue(any("closing balance" in w for w in warnings))
        self.assertEqual(summary["total_debit"], 200.0)

    def test_corrupt_and_blank_pdfs_fail_clearly(self):
        bad = self.tmp / "bad.pdf"
        bad.write_bytes(b"%PDF-1.4\nthis is not a pdf")
        with self.assertRaises(ExtractionError) as c:
            read_document(bad, "pdf", self.settings)
        self.assertEqual(c.exception.code, "pdf_corrupt")
        from reportlab.pdfgen import canvas
        blank = self.tmp / "blank.pdf"
        cv = canvas.Canvas(str(blank))
        cv.showPage()
        cv.save()
        with self.assertRaises(ExtractionError) as c:
            bank.extract_bank_statement(read_document(blank, "pdf", self.settings))
        self.assertEqual(c.exception.code, "no_transactions_found")

    def test_too_many_pages(self):
        from reportlab.pdfgen import canvas
        p = self.tmp / "many.pdf"
        cv = canvas.Canvas(str(p))
        for _ in range(6):
            cv.drawString(50, 50, "x")
            cv.showPage()
        cv.save()
        with self.assertRaises(ExtractionError) as c:
            read_document(p, "pdf", self.settings)
        self.assertEqual(c.exception.code, "too_many_pages")


@unittest.skipUnless(OCR, "Tesseract not installed")
class TestBankOCR(Base):
    def _check(self, path):
        r = self.bank_result(path)
        self.assertTrue(r["extraction"]["ocr_used"])
        tx = r["transactions"]
        self.assertEqual(len(tx), 6)
        self.assertEqual([t["debit"] for t in tx], [450.0, None, 2000.0, 12500.5, None, 1234.0])
        self.assertEqual([t["credit"] for t in tx], [None, 50000.0, None, None, 125.75, None])
        self.assertEqual(tx[-1]["balance"], 43941.25)
        self.assertTrue(all(t["ocr_confidence"] is not None for t in tx))

    def test_scanned_pdf(self):
        p = self.tmp / "scan.pdf"
        synth.pdf_to_scanned(self.bank_pdf, p)
        self._check(p)

    def test_skewed_scan(self):
        p = self.tmp / "skew.pdf"
        synth.pdf_to_scanned(self.bank_pdf, p, rotate_deg=2.0)
        self._check(p)

    def test_unreadable_image_gives_clear_error(self):
        from PIL import Image
        p = self.tmp / "blank.png"
        Image.new("RGB", (800, 800), "white").save(p)
        with self.assertRaises(ExtractionError) as c:
            read_document(p, "image", self.settings)
        self.assertEqual(c.exception.code, "unreadable_image")


class TestExport(Base):
    def test_bank_xlsx_reflects_edits_and_types(self):
        r = self.bank_result()
        r["transactions"][0]["description"] = "EDITED BY USER"
        r["transactions"][0]["debit"] = 999.99
        data, name, mime = ex.export_result(r, "xlsx")
        self.assertTrue(name.endswith(".xlsx"))
        wb = load_workbook(io.BytesIO(data))
        self.assertEqual(wb.sheetnames, ["Transactions", "Summary"])
        ws = wb["Transactions"]
        self.assertEqual(ws["C2"].value, "EDITED BY USER")
        self.assertEqual(ws["F2"].value, 999.99)
        self.assertEqual(ws["A2"].is_date, True)
        self.assertEqual(ws.freeze_panes, "A2")
        self.assertTrue(ws.auto_filter.ref.startswith("A1:"))
        self.assertTrue(str(ws["F9"].value).startswith("=SUM"))
        self.assertEqual(wb["Summary"]["B2"].value, r["metadata"]["bank_name"])

    def test_bank_csv_uses_edited_rows(self):
        r = self.bank_result()
        r["transactions"][1]["credit"] = 51000.0
        data, name, _ = ex.export_result(r, "csv")
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
        self.assertEqual(rows[0][0], "Transaction Date")
        self.assertEqual(rows[2][6], "51000.00")
        self.assertEqual(rows[1][0], "2025-04-01")

    def test_formula_injection_is_neutralised(self):
        r = self.bank_result()
        r["transactions"][0]["description"] = '=HYPERLINK("http://evil","x")'
        r["transactions"][1]["description"] = "+cmd|' /C calc'!A0"
        r["transactions"][2]["description"] = 'comma, "quote"\nnewline'
        csv_bytes, _, _ = ex.export_result(r, "csv", bom=False)
        text = csv_bytes.decode("utf-8")
        parsed = list(csv.reader(io.StringIO(text)))
        self.assertTrue(parsed[1][2].startswith("'="))
        self.assertTrue(parsed[2][2].startswith("'+"))
        self.assertEqual(parsed[3][2], 'comma, "quote"\nnewline')
        xl, _, _ = ex.export_result(r, "xlsx")
        c = load_workbook(io.BytesIO(xl))["Transactions"]["C2"]
        self.assertEqual(c.data_type, "s")  # stored as text, never evaluated
        self.assertEqual(c.value, '=HYPERLINK("http://evil","x")')

    def test_invoice_exports(self):
        p = self.tmp / "inv.pdf"
        synth.make_invoice_pdf(p)
        r = invoice_service.extract_invoice(read_document(p, "pdf", self.settings, want_tables=True))
        data, _, _ = ex.export_result(r, "xlsx")
        wb = load_workbook(io.BytesIO(data))
        self.assertEqual(wb.sheetnames, ["Invoice Details", "Line Items", "Summary"])
        self.assertEqual(wb["Line Items"]["I2"].value, 1000.0)
        with self.assertRaises(AppError):
            ex.export_result(r, "csv")  # needs part
        z, name, _ = ex.export_result(r, "zip")
        self.assertEqual(sorted(zipfile.ZipFile(io.BytesIO(z)).namelist()), ["invoice_details.csv", "invoice_line_items.csv"])
        d, _, _ = ex.export_result(r, "csv", part="line_items")
        self.assertIn("Widget A", d.decode("utf-8-sig"))

    def test_tables_selected_only_and_text_preserved(self):
        res = {"tool": "tables", "tables": [
            {"id": "1", "name": "A", "columns": ["Code", "Qty"], "rows": [["00123", "1,234.50"], ["=1+1", "7"]], "selected": True},
            {"id": "2", "name": "B", "columns": ["x"], "rows": [["y"]], "selected": False}]}
        data, _, _ = ex.export_result(res, "xlsx")
        wb = load_workbook(io.BytesIO(data))
        self.assertEqual(wb.sheetnames, ["A"])
        self.assertEqual(wb["A"]["A2"].value, "00123")  # leading zeros preserved
        self.assertEqual(wb["A"]["B2"].value, 1234.5)
        self.assertEqual(wb["A"]["A3"].data_type, "s")
        res["tables"][0]["selected"] = False
        with self.assertRaises(AppError):
            ex.export_result(res, "xlsx")


class TestOtherTools(Base):
    def test_invoice_fields(self):
        p = self.tmp / "inv.pdf"
        synth.make_invoice_pdf(p)
        r = invoice_service.extract_invoice(read_document(p, "pdf", self.settings, want_tables=True))
        f = r["fields"]
        self.assertEqual(f["invoice_number"], "INV-2025-001")
        self.assertEqual(f["invoice_date"], "2025-04-05")
        self.assertEqual(f["due_date"], "2025-04-20")
        self.assertEqual(f["supplier_tax_id"], "27ABCDE1234F1Z5")
        self.assertEqual(f["customer_tax_id"], "27PQRSX9876L1Z2")
        self.assertEqual((f["cgst"], f["sgst"], f["grand_total"]), (225.0, 225.0, 2950.0))
        self.assertEqual(len(r["line_items"]), 2)
        self.assertEqual(r["line_items"][0]["hsn_sac"], "8471")
        self.assertFalse([w for w in r["warnings"] if "add up" in w])

    def test_invoice_validation_flags_wrong_total(self):
        fields = {k: None for k in invoice_service.FIELD_KEYS}
        fields.update(invoice_number="A1", invoice_date="2025-01-01", subtotal=100.0, cgst=9.0, sgst=9.0, grand_total=150.0)
        warnings, calc = invoice_service.validate_invoice(fields, [{"line_total": 90.0}])
        self.assertEqual(calc["computed_grand_total"], 118.0)
        self.assertEqual(len([w for w in warnings if "grand total" in w or "subtotal" in w]), 2)

    def test_receipt(self):
        p = self.tmp / "rc.pdf"
        synth.make_receipt_pdf(p)
        row, items = receipt_service.extract_receipt(read_document(p, "pdf", self.settings), "rc.pdf")
        self.assertEqual((row["merchant"], row["receipt_number"], row["date"], row["time"]), ("FICTIONAL CAFE", "4521", "2025-05-12", "14:32"))
        self.assertEqual((row["subtotal"], row["tax"], row["total"], row["payment_method"]), (200.0, 10.0, 210.0, "UPI"))
        self.assertEqual(len(items), 3)
        self.assertEqual(row["flags"], [])

    @unittest.skipUnless(OCR, "Tesseract not installed")
    def test_receipt_image_ocr(self):
        pdf, png = self.tmp / "rc.pdf", self.tmp / "rc.png"
        synth.make_receipt_pdf(pdf)
        synth.pdf_page_to_png(pdf, png, dpi=300)
        row, items = receipt_service.extract_receipt(read_document(png, "image", self.settings), "rc.png")
        self.assertEqual(row["total"], 210.0)
        self.assertEqual(row["date"], "2025-05-12")
        self.assertIsNotNone(row["ocr_confidence"])

    def test_tables(self):
        p = self.tmp / "tb.pdf"
        synth.make_table_pdf(p)
        r = table_service.extract_tables(read_document(p, "pdf", self.settings, want_tables=True))
        self.assertEqual(r["tables"][0]["columns"], ["Item", "Stock", "Price"])
        self.assertEqual(r["tables"][0]["rows"][1], ["Notebook", "45", "42.00"])


class TestJobsAndPipeline(Base):
    def make_job(self, store, pdf=None, tool="bank_statement"):
        data = (pdf or self.bank_pdf).read_bytes()
        return store.create(tool, [("pdf", "pdf", "my statement.pdf", data)])

    def test_upload_to_edit_to_export_workflow(self):
        store = JobStore(self.settings)
        job = self.make_job(store)
        run_job(job, self.settings)
        self.assertEqual(job.status, "done", job.error)
        self.assertEqual(job.control.pages_done, job.control.pages_total)
        res = job.result
        patched = {"transactions": [dict(t) for t in res["transactions"]]}
        patched["transactions"][0]["description"] = "USER CORRECTION"
        patched["transactions"][0]["debit"] = "1,000.00"
        job.result = apply_patch(res, patched)
        self.assertIn("balance_mismatch", job.result["transactions"][0]["flags"])  # edit is re-validated
        data, _, _ = ex.export_result(job.result, "xlsx")
        ws = load_workbook(io.BytesIO(data))["Transactions"]
        self.assertEqual((ws["C2"].value, ws["F2"].value), ("USER CORRECTION", 1000.0))

    def test_patch_rejects_bad_numbers(self):
        store = JobStore(self.settings)
        job = self.make_job(store)
        run_job(job, self.settings)
        bad = {"transactions": [dict(job.result["transactions"][0], debit="abc")]}
        with self.assertRaises(AppError) as c:
            apply_patch(job.result, bad)
        self.assertEqual(c.exception.code, "invalid_number")

    def test_token_required_and_ids_are_random(self):
        store = JobStore(self.settings)
        job = self.make_job(store)
        self.assertEqual(store.get(job.id, job.token).id, job.id)
        for bad in (None, "", "wrong-token"):
            with self.assertRaises(AppError) as c:
                store.get(job.id, bad)
            self.assertEqual(c.exception.status, 404)
        with self.assertRaises(AppError):
            store.get("nonexistent", job.token)
        self.assertNotIn("statement", job.files[0].path.name)  # user filename never used on disk

    def test_delete_and_expiry_remove_files(self):
        store = JobStore(self.settings)
        j1, j2 = self.make_job(store), self.make_job(store)
        self.assertTrue(j1.files[0].path.exists())
        store.delete(j1.id)
        self.assertFalse(j1.files[0].path.exists())
        j2.expires_at = time.time() - 1
        self.assertEqual(store.purge_expired(), 1)
        self.assertFalse(j2.files[0].path.parent.exists())
        with self.assertRaises(AppError):
            store.get(j2.id, j2.token)

    def test_failed_job_has_safe_error(self):
        store = JobStore(self.settings)
        bad = self.tmp / "bad2.pdf"
        bad.write_bytes(b"%PDF-1.4 broken")
        job = self.make_job(store, bad)
        run_job(job, self.settings)
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error["code"], "pdf_corrupt")
        self.assertNotIn(str(self.tmp), job.error["message"])

    def test_cancel_stops_processing(self):
        store = JobStore(self.settings)
        job = self.make_job(store)
        job.control.cancelled.set()
        run_job(job, self.settings)
        self.assertEqual(job.status, "cancelled")

    def test_receipt_batch_isolates_failures(self):
        store = JobStore(self.settings)
        good = self.tmp / "rc.pdf"
        synth.make_receipt_pdf(good)
        bad = b"%PDF-1.4 broken"
        job = store.create("receipt", [("pdf", "pdf", "good.pdf", good.read_bytes()), ("pdf", "pdf", "bad.pdf", bad)])
        run_job(job, self.settings)
        self.assertEqual(job.status, "done")
        self.assertEqual(len(job.result["receipts"]), 1)
        self.assertEqual(job.result["failed_files"][0]["filename"], "bad.pdf")
        data, _, _ = ex.export_result(job.result, "xlsx")
        self.assertEqual(load_workbook(io.BytesIO(data))["Receipts"]["I2"].value, 210.0)


if __name__ == "__main__":
    unittest.main()
