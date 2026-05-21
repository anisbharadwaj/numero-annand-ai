import os
import time
import logging
from typing import Optional

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import SessionLocal, User, init_db
from auth import hash_password, verify_password, create_access_token, decode_token

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("anis-ai-shield")

# -----------------------------
# Environment
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-render")
ADMIN_LOGIN_ID = os.getenv(
    "ADMIN_LOGIN_ID",
    "https://protected-ethical-anis-ai-12.onrender.com"
)
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

VERCEL_URL = os.getenv(
    "VERCEL_URL",
    "https://anis-ai-shield.vercel.app"
)

SERVER_START_TIME = time.time()

# -----------------------------
# Gemini setup
# -----------------------------
ai_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Gemini AI initialized successfully.")
    except Exception as e:
        logger.error(f"Gemini init failed: {e}")
        ai_model = None
else:
    logger.warning("GEMINI_API_KEY not set. AI will not work until configured.")

# -----------------------------
# App
# -----------------------------
app = FastAPI(title="Anis-AI-Shield", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        VERCEL_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# DB init
# -----------------------------
init_db()


class ChatMessage(BaseModel):
    message: str


@app.on_event("startup")
def startup_event():
    logger.info("Anis-AI-Shield backend started.")
    logger.info(f"ADMIN_LOGIN_ID: {ADMIN_LOGIN_ID}")
    logger.info(f"VERCEL_URL: {VERCEL_URL}")


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": "Anis-AI-Shield",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - SERVER_START_TIME, 2),
        "version": "2.0.0",
        "ai_connected": bool(GEMINI_API_KEY and ai_model),
    }


@app.post("/api/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: str = Form(...),
):
    if captcha_verified.lower() != "true":
        raise HTTPException(status_code=403, detail="Human verification required.")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            logger.warning(f"Failed login attempt: unknown username={username}")
            raise HTTPException(status_code=401, detail="Invalid Render URL or password.")

        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt: username={username}")
            raise HTTPException(status_code=401, detail="Invalid Render URL or password.")

        token = create_access_token(
            {
                "sub": username,
                "role": "admin",
                "username": username,
            }
        )

        logger.info(f"Login success: username={username}")
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    finally:
        db.close()


@app.post("/api/chat")
def chat(payload: ChatMessage, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token.")

    token = authorization.split(" ", 1)[1]
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid token.")

    if not ai_model:
        raise HTTPException(status_code=503, detail="AI core not configured.")

    try:
        response = ai_model.generate_content(payload.message)
        reply_text = getattr(response, "text", None) or "No AI response returned."
        return {"reply": reply_text}
    except Exception as e:
        logger.error(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="AI processing failed.")
