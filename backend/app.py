from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from ingestion.ingest_api import validate_and_store
from monitoring.telemetry_watcher import start_watcher

app = FastAPI(title="Protected Ethical Anis AI")

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    # validate schema and store rows
    result = await validate_and_store(file)
    return {"status":"accepted","rows": result["rows"], "job_id": result["job_id"]}

@app.post("/run_audit/{job_id}")
async def run_audit(job_id: str):
    # compute metrics and store audit record
    from metrics.fairness import compute_fairness_metrics
    from metrics.reliability import compute_reliability_metrics
    fairness = compute_fairness_metrics(job_id)
    reliability = compute_reliability_metrics(job_id)
    # store and return summary id
    return {"audit_id": job_id, "fairness": fairness, "reliability": reliability}

# Start background telemetry watcher
@app.on_event("startup")
def startup_event():
    start_watcher()
