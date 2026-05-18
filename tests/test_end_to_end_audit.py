# tests/test_end_to_end_audit.py
import os
import time
import requests
import pytest

BASE = "http://127.0.0.1:8000"

def test_ingest_and_run_audit():
    sample = "tests/fixtures/sample.csv"
    assert os.path.exists(sample), "Sample fixture missing; run tests/generate_sample.py"
    with open(sample, "rb") as f:
        r = requests.post(f"{BASE}/ingest", files={"file": f})
    assert r.status_code in (200,201), f"ingest failed: {r.status_code} {r.text}"
    job_id = r.json().get("job_id") or r.json().get("rows") or "sample-job"
    # allow backend a moment to process
    time.sleep(2)
    r2 = requests.post(f"{BASE}/run_audit/{job_id}")
    assert r2.status_code in (200,201), f"run_audit failed: {r2.status_code} {r2.text}"
    body = r2.json()
    assert "fairness" in body or "reliability" in body, "audit response missing expected keys"
