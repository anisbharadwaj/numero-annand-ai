# tests/test_ingest_schema.py
import os
import io
import csv
import pandas as pd
import pytest

# Adjust import path to your validators module
try:
    from backend.ingestion.validators import validate_schema, REQUIRED_COLUMNS, MIN_SAMPLE
except Exception as e:
    raise RuntimeError("Unable to import validators: " + str(e))

def make_df_missing_cols():
    # create a DataFrame missing required columns
    return pd.DataFrame({"unique_id": [1, 2, 3]})

def make_small_df():
    # create a DataFrame with required columns but too few rows
    rows = [
        {
            "unique_id": "1",
            "input_text": "a",
            "model_output": "0",
            "timestamp": "2025-01-01T00:00:00Z",
            "user_region": "RegionA",
            "user_gender": "male",
            "ground_truth": "0"
        }
    ]
    return pd.DataFrame(rows)

def make_valid_df(n=MIN_SAMPLE):
    # create a valid DataFrame with n rows
    rows = []
    for i in range(n):
        rows.append({
            "unique_id": str(i),
            "input_text": f"sample {i}",
            "model_output": "0",
            "ground_truth": "0",
            "timestamp": "2025-01-01T00:00:00Z",
            "user_region": "RegionA",
            "user_gender": "male",
            "confidence": 0.9,
            "api_key": "test-key"
        })
    return pd.DataFrame(rows)

def test_validate_schema_missing_columns():
    df = make_df_missing_cols()
    with pytest.raises(ValueError) as exc:
        validate_schema(df)
    assert "Missing columns" in str(exc.value)

def test_validate_schema_sample_too_small():
    df = make_small_df()
    # If validate_schema raises ValueError for small sample, assert message
    with pytest.raises(ValueError) as exc:
        validate_schema(df)
    assert "Sample too small" in str(exc.value)

def test_validate_schema_valid():
    df = make_valid_df(n=1000)
    # Should not raise
    assert validate_schema(df) is True
