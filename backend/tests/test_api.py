"""HTTP-level tests. Needs: pip install -r requirements-dev.txt  (skipped automatically without FastAPI)."""
import dataclasses
import io
import tempfile
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from tests import synth  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    s = dataclasses.replace(get_settings(), jobs_dir=tmp_path / "jobs", max_upload_mb=1, rate_limit_per_minute=100)
    with TestClient(create_app(s)) as c:
        yield c


@pytest.fixture()
def bank_pdf(tmp_path):
    p = tmp_path / "bank.pdf"
    synth.make_bank_statement_pdf(p)
    return p.read_bytes()


def _wait(client, job_id, token):
    for _ in range(120):
        r = client.get(f"/api/v1/jobs/{job_id}", headers={"X-Job-Token": token})
        if r.json()["status"] in ("done", "failed", "cancelled"):
            return r.json()
        time.sleep(0.5)
    raise AssertionError("job did not finish")


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_full_workflow(client, bank_pdf):
    r = client.post("/api/v1/jobs", data={"tool": "bank_statement"}, files={"files": ("s.pdf", bank_pdf, "application/pdf")})
    assert r.status_code == 202
    job, token = r.json()["job_id"], r.json()["token"]
    h = {"X-Job-Token": token}
    assert _wait(client, job, token)["status"] == "done"
    res = client.get(f"/api/v1/jobs/{job}/result", headers=h).json()
    assert len(res["transactions"]) == 6
    res["transactions"][0]["description"] = "EDITED"
    patched = client.patch(f"/api/v1/jobs/{job}/result", headers=h, json={"result": res})
    assert patched.status_code == 200
    x = client.post(f"/api/v1/jobs/{job}/export", headers=h, json={"format": "xlsx"})
    assert x.status_code == 200 and "attachment" in x.headers["content-disposition"]
    assert load_workbook(io.BytesIO(x.content))["Transactions"]["C2"].value == "EDITED"
    assert client.get(f"/api/v1/jobs/{job}/files/0", headers=h).headers["content-type"] == "application/pdf"
    assert client.delete(f"/api/v1/jobs/{job}", headers=h).status_code == 204
    assert client.get(f"/api/v1/jobs/{job}", headers=h).status_code == 404


def test_private_results_need_the_token(client, bank_pdf):
    r = client.post("/api/v1/jobs", data={"tool": "bank_statement"}, files={"files": ("s.pdf", bank_pdf, "application/pdf")}).json()
    for hdrs in ({}, {"X-Job-Token": "nope"}):
        assert client.get(f"/api/v1/jobs/{r['job_id']}/result", headers=hdrs).status_code == 404
        assert client.get(f"/api/v1/jobs/{r['job_id']}/files/0", headers=hdrs).status_code == 404


def test_rejects_bad_uploads(client):
    r = client.post("/api/v1/jobs", data={"tool": "bank_statement"}, files={"files": ("a.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 415 and r.json()["error"]["code"] == "unsupported_type"
    big = b"%PDF-" + b"0" * (2 * 1024 * 1024)
    assert client.post("/api/v1/jobs", data={"tool": "tables"}, files={"files": ("a.pdf", big, "application/pdf")}).status_code == 413
    assert client.post("/api/v1/jobs", data={"tool": "nope"}, files={"files": ("a.pdf", b"%PDF-", "application/pdf")}).status_code == 400


def test_rate_limit(tmp_path):
    s = dataclasses.replace(get_settings(), jobs_dir=tmp_path / "j", rate_limit_per_minute=2)
    with TestClient(create_app(s)) as c:
        codes = [c.post("/api/v1/jobs", data={"tool": "tables"}, files={"files": ("a.pdf", b"x", "application/pdf")}).status_code for _ in range(3)]
    assert codes[-1] == 429
