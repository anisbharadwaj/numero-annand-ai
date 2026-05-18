# backend/tests/conftest.py
# Pytest fixtures for Protected Ethical Anis AI tests
import os
import shutil
import tempfile
import sqlite3
import csv
import time
import uuid
import random
import pytest
from fastapi.testclient import TestClient

# Ensure tests import the app from the correct module path
# Adjust import path if your FastAPI app object lives elsewhere
try:
    from backend.app import app
except Exception as e:
    raise RuntimeError("Unable to import backend.app: " + str(e))

# Default sample fixture path used by tests
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_PATH = os.path.join(SAMPLE_DIR, "sample.csv")

@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures():
    """
    Ensure tests/fixtures/sample.csv exists. If not present, generate a synthetic sample.
    This keeps CI and local runs deterministic without external data.
    """
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    if not os.path.exists(SAMPLE_PATH):
        # generate a minimal synthetic dataset with required schema and >=1000 rows
        regions = ['RegionA', 'RegionB', 'RegionC']
        genders = ['male', 'female', 'other']
        with open(SAMPLE_PATH, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "unique_id",
                "input_text",
                "model_output",
                "ground_truth",
                "timestamp",
                "user_region",
                "user_gender",
                "confidence",
                "api_key"
            ])
            for i in range(1200):
                uid = str(uuid.uuid4())
                text = f"sample input {i}"
                gt = random.choice([0, 1])
                pred = gt if random.random() > 0.15 else 1 - gt
                ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                w.writerow([uid, text, str(pred), str(gt), ts, random.choice(regions), random.choice(genders), round(random.random(), 2), 'test-key'])
    yield SAMPLE_PATH
    # no teardown for fixture file; keep for subsequent runs

@pytest.fixture(scope="function")
def client(monkeypatch, tmp_path):
    """
    Provide a TestClient configured to use an in-memory SQLite DB (or a temp file DB)
    so tests do not touch production data.
    """
    # Configure environment variables expected by your app to use test DB
    # Example: BACKEND_DATABASE_URL or similar. Adjust to your app's config.
    # If your app reads a DATABASE_URL env var, set it to sqlite in-memory.
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    # If your app requires other env vars for test mode:
    monkeypatch.setenv("ENV", "test")
    # Create TestClient
    test_client = TestClient(app)
    yield test_client
    # cleanup if needed (TestClient context handles shutdown)

@pytest.fixture
def sample_path(ensure_fixtures):
    return ensure_fixtures
