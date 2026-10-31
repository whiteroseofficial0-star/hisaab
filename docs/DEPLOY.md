# Deployment (VPS)

Not deployed or verified by the authors of this repository; follow and adapt.

1. **Server:** Ubuntu LTS VPS, 2+ vCPU / 2-4 GB RAM (OCR is CPU and memory hungry). Serverless platforms with short execution limits are a poor fit for OCR jobs.
2. **Install:** Docker + Compose plugin. `git clone <your-repo>`; `cp .env.example .env` and set `CORS_ORIGINS=https://your-domain`, `SITE_URL=https://your-domain`.
3. **Run:** `docker compose up -d --build`. Backend has a health check (`/api/v1/health`).
4. **HTTPS:** put a reverse proxy in front (Caddy or nginx + certbot) on 443 proxying to the frontend container's port 8080. Set `client_max_body_size` >= `MAX_UPLOAD_MB * MAX_BATCH_FILES`, and forward the real client IP (`X-Forwarded-For`) if you want per-IP rate limiting to see it (add trusted-proxy handling before relying on it).
5. **Domain/DNS:** A/AAAA records to the VPS. Then follow `docs/SEO.md`.
6. **Resource limits:** `MAX_CONCURRENCY` (OCR workers), `mem_limit`/`cpus` in `docker-compose.yml`, `MAX_PDF_PAGES`, `JOB_TIMEOUT_SECONDS`.
7. **Retention:** uploads live in `/data/jobs` (tmpfs by default, so a restart wipes them). Backups should exclude it. `RETENTION_MINUTES` controls expiry.
8. **Logs/monitoring:** `docker compose logs -f backend`; point an uptime monitor at `/api/v1/health`. Logs contain error types only, not document data.
9. **Update:** `git pull && docker compose up -d --build`; in-flight jobs are lost on restart.
