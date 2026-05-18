from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Protected Ethical Anis AI",
    description="Ethical and protected AI monitoring system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Protected Ethical Anis AI Running Successfully"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/metrics")
def metrics():
    return {
        "fairness": "stable",
        "reliability": "high",
        "security": "protected"
    }
