# Architecture

```
React (Vite) ──/api/v1──> FastAPI ──> ThreadPool workers ──> pipeline.run_job
                              │                                  │
                         JobStore (memory + private temp dir)    ├─ document_service  (PDF text / OCR per page)
                                                                 ├─ ocr_service       (OpenCV preprocess + Tesseract)
                                                                 ├─ bank_statement_service / invoice_service /
                                                                 │  receipt_service / table_service
                                                                 └─ export_service    (openpyxl, csv, zip)
```
- **Per-page strategy:** a PDF page with at least 8 selectable words is read as text; otherwise it is rendered (default 300 dpi), straightened (projection-profile deskew ±5°), contrast-adjusted if flat, and OCR'd with per-word confidence.
- **Bank parser:** words → lines → rows. Rows start with a date; trailing two-decimal amounts are assigned to debit/credit/balance by header column position, falling back to Cr/Dr suffix or running-balance arithmetic. If direction cannot be established nothing is guessed: the row is flagged `missing_amount` and its source text is kept.
- **Validation** (`validate_transactions`) also runs after every user edit (PATCH), so flags stay truthful.
- **Jobs:** random 128-bit id + separate secret token (`X-Job-Token`); wrong/missing/expired all return 404. Files stored as `input_N.ext` under `JOBS_DIR/<job>`; a cleanup thread removes expired jobs and orphan folders. Progress is real (`pages_done/pages_total`); cancellation and timeout are checked between pages.
- **Why not SQLite/Redis:** jobs are short-lived and privacy-sensitive, so results are held in memory and expire; restarting the server drops them. To persist or scale out, replace `JobStore` and the thread pool (queue + worker); PostgreSQL would hold job metadata only, never document contents by default.
- **Why not PyMuPDF:** AGPL. pdfplumber + pypdfium2 are permissive.
- **Frontend:** client-rendered SPA; per-route title/description/canonical/JSON-LD are set at runtime (`useSeo`). See `docs/SEO.md` for the prerendering caveat.
