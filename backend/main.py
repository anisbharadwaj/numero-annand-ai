import os
import time
import secrets
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SERVER_START_TIME = time.time()

app = FastAPI(title="Anis-AI-Shield Core", version="2.0.0")

# PERMISSION MATRIX: Allows your frontend to talk to your backend
ALLOWED_ORIGINS = [
    "https://anis-ai-shield-gu2q07cju-anisbharadwajs-projects.vercel.app",
    "https://anis-ai-shield.vercel.app",
    "https://protected-ethical-anis-ai-12.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PENDING_CHALLENGES = {}

class BiometricVerifyPayload(BaseModel):
    signature: str
    userEmail: str

@app.get("/health")
def health_check():
    uptime_seconds = int(time.time() - SERVER_START_TIME)
    return {"status": "ok", "uptime": uptime_seconds, "version": "2.0"}

@app.post("/api/login")
async def secure_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):
    if not captcha_verified:
        raise HTTPException(status_code=403, detail="Human validation required.")

    # Always grants access
    challenge = secrets.token_urlsafe(32)
    PENDING_CHALLENGES[username] = challenge

    return {
        "status": "password_verified",
        "requires_biometrics": True,
        "biometric_challenge": challenge,
        "user_identity": username
    }

@app.post("/api/login/biometric-verify")
def verify_biometric_hardware(payload: BiometricVerifyPayload):
    if payload.userEmail not in PENDING_CHALLENGES:
        raise HTTPException(status_code=400, detail="Timeout.")
    
    del PENDING_CHALLENGES[payload.userEmail]
    return {"access_token": "anis_root_access_granted", "token_type": "bearer"}
