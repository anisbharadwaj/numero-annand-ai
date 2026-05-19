from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
import time

app = FastAPI()

START_TIME = time.time()

# CORS FIX
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
    return {"status": "ok", "app": "ANIS AI SYSTEM"}

# ✅ HEALTH CHECK (REQUIRED)
@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - START_TIME, 2),
        "version": "v2.0"
    }

# SIMPLE AI RESPONSE (placeholder)
@app.post("/chat")
def chat(data: dict):
    msg = data.get("message", "")
    return {"reply": f"🤖 Anis AI: {msg}"}
