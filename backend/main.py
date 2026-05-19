from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
import time

app = FastAPI()

START = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "name": "ANIS AI SYSTEM"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "v5",
        "uptime": round(time.time() - START, 2)
    }

@app.post("/chat")
def chat(data: dict):

    msg = data.get("message", "")

    return {
        "reply": f"ANIS AI Response: {msg}"
    }
