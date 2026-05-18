REQUIRED_COLUMNS = ["unique_id","input_text","model_output","timestamp","user_region","user_gender"]
MIN_SAMPLE = 1000

def validate_schema(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if df.shape[0] < MIN_SAMPLE:
        raise ValueError(f"Sample too small: {df.shape[0]} rows; need >= {MIN_SAMPLE}")
    return True
