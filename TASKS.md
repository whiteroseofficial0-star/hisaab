# Status: what was actually run

Authoring environment: Linux sandbox, Python 3.12, Tesseract 5.3.4, **no network** (could not `pip install` FastAPI/pytest or `npm install` anything). Therefore:

## Verified (actually executed, passing)
- 31 backend engine tests: `python -m unittest tests.test_engine` -> `Ran 31 tests ... OK` (plain `discover` also tries `test_api.py`, which needs pytest and FastAPI)
  - signature/size/empty/corrupt validation; digital bank PDF (2 pages, wrapped narrations, header repeated); **scanned** and **2-degree skewed** scanned PDFs through real Tesseract OCR (all 6 rows, debit/credit/balance correct); blank/corrupt/too-many-pages errors; balance mismatch and duplicate flags; Excel opens with edited values, real date/number cells, frozen header, filter, SUM totals; CSV uses edited data; formula injection neutralised (CSV and XLSX); invoice fields + line items (GST); receipt PDF and receipt **image OCR**; PDF tables; job tokens, deletion, expiry cleanup, cancellation, safe error messages; receipt batch isolating a bad file; upload->process->edit->re-validate->export workflow at the service level.

- Sitemap/robots generator: `SITE_URL=https://example.invalid node scripts/generate-seo-files.mjs` produced 21 URLs and a robots.txt with the Sitemap line.
- Frontend source parsed by the TypeScript compiler (v6.0.3) with third-party modules stubbed: no syntax errors and no type errors other than noise caused by the stubs. **This is not a real type-check** (React/Vite types were not installed).

## Written but NOT run
- FastAPI layer (`app/main.py`, `app/api/routes.py`, `app/schemas/api.py`) and `tests/test_api.py` - FastAPI not installable here. Expect to fix small issues on first run.
- Entire frontend (React/TS/Tailwind), Vitest tests, Playwright e2e - never compiled. `tsc` errors are likely; fix them first.
- Docker/Compose/nginx files, GitHub Actions workflow - never built or executed.
- Package versions not marked "(tested)" in `requirements.txt`, and all `package.json` versions, were pinned from memory and not installed.

## Known limitations
- Bank parser expects amounts with two decimals, rows starting with a date, and a header row for best debit/credit detection; reverse-chronological statements are flagged, not reordered. No per-bank templates.
- OCR accuracy depends on scan quality; digits can be misread (flagged by confidence and balance checks, never silently fixed).
- Invoice party names/addresses are heuristic; one invoice per upload; tax-inclusive layouts can trigger total warnings.
- Receipt line items and OCR table columns are best-effort. Password-protected PDFs are rejected with a clear message (no password flow).
- Jobs live in memory (lost on restart); no SQLite/PostgreSQL, no Redis/worker queue. Rate limiting is in-process and per-IP (needs trusted-proxy handling behind a proxy).
- Client-rendered site: see `docs/SEO.md` caveat. Ads: placeholder slot only, disabled by default.
- Playwright e2e covers bank statement and receipt flows only. No accessibility audit was run (keyboard/label/aria patterns were written in, not tested with a screen reader).
- Not deployed anywhere.
