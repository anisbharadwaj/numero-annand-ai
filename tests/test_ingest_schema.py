import pandas as pd
from backend.ingestion.validators import validate_schema
def test_validate_schema_missing_columns(tmp_path):
    df = pd.DataFrame({'unique_id':[1]})
    try:
        validate_schema(df)
        assert False, "Expected ValueError for missing columns"
    except ValueError as e:
        assert "Missing columns" in str(e)
