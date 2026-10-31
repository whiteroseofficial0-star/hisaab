# API (v1)

Interactive docs and schemas: `/api/docs` (OpenAPI at `/api/openapi.json`). Errors are always `{"error": {"code", "message"}}`.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | status, OCR availability, limits |
| POST | `/api/v1/jobs` | multipart: `tool` (`bank_statement` \| `invoice` \| `receipt` \| `tables`), `files`. Returns 202 `{job_id, token, status, expires_at}` |
| GET | `/api/v1/jobs/{id}` | status + genuine progress. Header `X-Job-Token` required on every job route |
| GET | `/api/v1/jobs/{id}/result` | 409 until `done` |
| PATCH | `/api/v1/jobs/{id}/result` | body `{"result": {...edited parts...}}`; re-validated, flags recomputed |
| POST | `/api/v1/jobs/{id}/export` | body `{"format": "xlsx\|csv\|zip", "part": "details\|line_items"?, "bom": true}` |
| GET | `/api/v1/jobs/{id}/files/{index}` | original upload (for preview) |
| DELETE | `/api/v1/jobs/{id}` | cancels and deletes files and results |

```bash
curl -F tool=bank_statement -F files=@statement.pdf http://localhost:8000/api/v1/jobs
curl -H "X-Job-Token: <token>" http://localhost:8000/api/v1/jobs/<job_id>
```
