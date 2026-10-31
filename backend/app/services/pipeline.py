"""Runs one job: reads the document(s), extracts, validates. Executed on a worker thread."""
from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.control import JobCancelled, JobTimeout
from app.core.errors import AppError, ExtractionError
from app.core.jobs import Job
from app.services import bank_statement_service as bank
from app.services import invoice_service, receipt_service, table_service
from app.services.document_service import read_document

log = logging.getLogger("hisaab.pipeline")


def run_job(job: Job, settings: Settings) -> None:
    ctl = job.control
    job.status = "processing"
    ctl.start()
    ctl.set_stage("reading")
    try:
        f0 = job.files[0]
        if job.tool == "bank_statement":
            pages = read_document(f0.path, f0.kind, settings, ctl)
            ctl.set_stage("parsing")
            job.result = bank.extract_bank_statement(pages)
        elif job.tool == "invoice":
            pages = read_document(f0.path, f0.kind, settings, ctl, want_tables=True)
            ctl.set_stage("parsing")
            job.result = invoice_service.extract_invoice(pages)
        elif job.tool == "tables":
            pages = read_document(f0.path, f0.kind, settings, ctl, want_tables=True)
            ctl.set_stage("parsing")
            job.result = table_service.extract_tables(pages)
        elif job.tool == "receipt":
            receipts, items, failed = [], [], []
            for sf in job.files:
                ctl.check()
                try:
                    pages = read_document(sf.path, sf.kind, settings, ctl, source=sf.index)
                    row, its = receipt_service.extract_receipt(pages, sf.safe_name)
                    receipts.append(row)
                    items += its
                except ExtractionError as e:  # one bad file must not fail the whole batch
                    failed.append({"filename": sf.safe_name, "code": e.code, "message": e.message})
            if not receipts:
                raise ExtractionError("no_receipts_extracted", "None of the files could be read. " +
                                      (failed[0]["message"] if failed else ""))
            job.result = {"tool": "receipt", "receipts": receipts, "line_items": items, "failed_files": failed,
                          "warnings": [f"{x['filename']}: {x['message']}" for x in failed],
                          "flag_messages": receipt_service.RECEIPT_FLAG_MESSAGES}
        else:
            raise ExtractionError("unknown_tool", "Unknown tool.")
        job.status = "done"
        ctl.set_stage("done")
    except JobCancelled:
        job.status = "cancelled"
    except JobTimeout:
        job.status, job.error = "failed", {"code": "timeout", "message": "Processing took too long and was stopped. Try a smaller file."}
    except AppError as e:
        job.status, job.error = "failed", {"code": e.code, "message": e.message}
    except Exception as e:  # never leak internals or document content
        log.error("job %s failed with %s", job.id[:6], type(e).__name__)
        job.status, job.error = "failed", {"code": "internal_error", "message": "Something went wrong while processing this file."}
