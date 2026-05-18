# tests/test_end_to_end_audit.py
import os
import time
import json
import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app object here. Adjust the import path if needed.
# Example: from backend.app import app
try:
    from backend.app import app
except Exception as e:
    raise RuntimeError("Unable to import backend.app: " + str(e))

client = TestClient(app)

SAMPLE_PATH = "tests/fixtures/sample.csv"

@pytest.fixture(scope="session", autouse=True)
def ensure_sample_fixture():
    assert os.path.exists(SAMPLE_PATH), "Sample fixture missing; run tests/generate_sample.py or add tests/fixtures/sample.csv"
    return SAMPLE_PATH

def test_ingest_and_run_audit_inprocess(ensure_sample_fixture):
    # Ingest the sample file
    with open(ensure_sample_fixture, "rb") as f:
        resp = client.post("/ingest", files={"file": ("sample.csv", f, "text/csv")}, timeout=30)
    assert resp.status_code in (200, 201), f"ingest failed: {resp.status_code} {resp.text}"
    body = resp.json()
    # job_id may be returned differently; handle common shapes
    job_id = body.get("job_id") or body.get("audit_id") or body.get("rows") or None
    assert job_id is not None, f"ingest response missing job_id: {json.dumps(body)}"

    # Allow a short processing window if backend does background work
    time.sleep(1)

    # Run audit synchronously
    resp2 = client.post(f"/run_audit/{job_id}", timeout=60)
    assert resp2.status_code in (200, 201), f"run_audit failed: {resp2.status_code} {resp2.text}"
    audit = resp2.json()
    # Basic expected keys
    assert ("fairness" in audit) or ("reliability" in audit), "audit response missing expected keys"

    # Example: check that flagged_examples were created (if your API returns them)
    # If your API stores flagged examples in DB, you can call a read endpoint or inspect returned summary
    # This is a placeholder assertion — adapt to your API's actual response shape
    if "flagged_examples" in audit:
        assert isinstance(audit["flagged_examples"], list)

    # PII safety check placeholder: ensure no raw emails present in returned JSON strings
    serialized = json.dumps(audit)
    assert "@example.com" not in serialized, "Potential PII leak detected in audit response"

