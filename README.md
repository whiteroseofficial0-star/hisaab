# Hisaab

**Convert Documents. Extract Data. Export to Excel.**

Open-source web app that turns bank statement PDFs, invoices (PDF or image), receipts and PDF tables into editable tables, then into real `.xlsx` / `.csv` files. Guest use only (no accounts, no payments), processed on your own server, not sent to third-party AI services.

> **Status: first release, partly verified.** See [TASKS.md](TASKS.md) for exactly what was run and what was not. In particular the frontend was written but **not compiled or tested** in the environment it was authored in; run the commands below to verify it on your machine.

## Features
- Bank statement PDF → transactions (digital PDFs via text extraction, scanned PDFs via Tesseract OCR with OpenCV clean-up), balance reconciliation, duplicate and mismatch flags, editable table, Excel + CSV export
- Invoice PDF/image → details + line items (generic and Indian GST), totals checks
- Receipts (batch up to 10) → one row per receipt + line items; failed files reported
- PDF tables → every table separately, edit, choose, export (XLSX sheets / CSV / ZIP)
- Job tokens, expiry, deletion, rate limiting, formula-injection-safe exports

## Quick start on Windows 11 (PowerShell)
```powershell
# 1. Tools (or install them manually)
winget install Git.Git OpenJS.NodeJS.LTS Python.Python.3.12 UB-Mannheim.TesseractOCR
# Docker is optional: winget install Docker.DockerDesktop
# Close and reopen PowerShell so PATH updates.

# 2. Backend
cd hisaab\backend
python -m venv .venv
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # once, to allow venv activation
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
# If tesseract is not on PATH:
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
python -m uvicorn app.main:app --reload --port 8000

# 3. Frontend (second PowerShell window)
cd hisaab\frontend
npm install
npm run dev          # open http://localhost:5173
```
API docs: http://localhost:8000/api/docs

## Tests
```powershell
cd backend ; python -m pytest                 # engine + API tests (engine tests only, no pytest needed: python -m unittest tests.test_engine)
cd ..\frontend ; npx tsc --noEmit ; npm test  # type check + Vitest
cd .. ; python scripts\make_samples.py        # writes FICTIONAL sample PDFs/images to .\samples
cd frontend ; npx playwright install chromium ; npm run e2e
```
Scanned-document tests need Tesseract (they are skipped automatically if it is missing).

## Docker
```powershell
copy .env.example .env      # adjust values; placeholders only
docker compose up --build   # http://localhost:8080
```

## Configuration
All settings are environment variables; see [.env.example](.env.example): upload size, page limit, batch size, timeout, retention, concurrency, rate limit, CORS origins, OCR language and DPI, `TESSERACT_CMD`.
Frontend build variables: `VITE_SITE_URL` (canonical URLs, sitemap), `VITE_API_BASE` (if the API is on another origin), `VITE_CONTACT_EMAIL`, `VITE_ADS_ENABLED` (off by default; no ad code included).

For production SEO, use `npm run build:seo` in `frontend/` with `SITE_URL` and `VITE_SITE_URL` set. It builds the site, writes `sitemap.xml` / `robots.txt`, then prerenders every public route to static HTML (requires Chrome or `PRERENDER_EXECUTABLE`). See [docs/SEO.md](docs/SEO.md) for the full setup and keyword structure.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Tesseract OCR is not installed or not on PATH` | Install it and/or set `TESSERACT_CMD`; check `/api/v1/health` shows `ocr_available: true` |
| `OCR language data 'xxx' is not installed` | Install the language pack and set `OCR_LANG` (e.g. `eng+hin`) |
| Scanned page returns nothing | Rescan at 300 dpi, straight, high contrast; see the OCR guide in the app |
| `Port already in use` | `netstat -ano \| findstr :8000` then stop the process, or use `--port 8001` and set `VITE_API_BASE` / the Vite proxy |
| CORS error in browser | Add the exact frontend origin to `CORS_ORIGINS` |
| `running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

## More
[Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [Deployment](docs/DEPLOY.md) · [SEO setup](docs/SEO.md) · [Security](SECURITY.md) · [Third-party licenses](THIRD_PARTY.md) · [Contributing](CONTRIBUTING.md)

To publish: create an empty repository on your Git host, then `git init`, `git add .`, `git commit -m "Initial commit"`, `git remote add origin <your-repo-url>`, `git push -u origin main`.

License: MIT (see [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md)).
