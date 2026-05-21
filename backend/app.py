import os
import time
import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Form, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google import genai
from google.genai import types

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("ANIS-AI-SHIELD")

# =========================
# GLOBAL STATE
# =========================

ai_client = None
model_ready = False

SERVER_START_TIME = time.time()

# =========================
# ENV VARIABLES
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "anis-secret")

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "https://protected-ethical-anis-ai-12.onrender.com"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "AnisSecure2026"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# FASTAPI LIFESPAN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global ai_client
    global model_ready

    logger.info("Starting ANIS-AI-SHIELD")

    try:

        if GEMINI_API_KEY:

            ai_client = genai.Client(
                api_key=GEMINI_API_KEY
            )

            model_ready = True

            logger.info("Gemini AI Connected")

        else:

            logger.warning("No GEMINI_API_KEY Found")

    except Exception as e:

        logger.error(f"AI INIT ERROR: {e}")

    yield

    logger.info("Shutting down server")

# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="ANIS-AI-SHIELD",
    version="3.0",
    lifespan=lifespan
)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# REQUEST MODELS
# =========================

class ChatRequest(BaseModel):
    message: str

# =========================
# READY ENDPOINT
# =========================

@app.get("/ready")
async def ready():
    return {
        "status": "ready"
    }

# =========================
# HEALTH ENDPOINT
# =========================

@app.get("/health")
async def health():

    uptime = int(time.time() - SERVER_START_TIME)

    return {
        "status": "online",
        "uptime": uptime,
        "ai_initialized": model_ready,
        "server": "ANIS-AI-SHIELD"
    }

# =========================
# LOGIN ENDPOINT
# =========================

@app.post("/api/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):

    if not captcha_verified:

        raise HTTPException(
            status_code=403,
            detail="Human verification required"
        )

    if username != ADMIN_USERNAME:

        raise HTTPException(
            status_code=401,
            detail="Invalid Render URL"
        )

    if password != ADMIN_PASSWORD:

        raise HTTPException(
            status_code=401,
            detail="Invalid Password"
        )

    return {
        "success": True,
        "message": "Login successful",
        "token": "anis_ai_access"
    }

# =========================
# AI CHAT ENDPOINT
# =========================

@app.post("/api/chat")
async def chat(
    payload: ChatRequest,
    authorization: str = Header(None)
):

    if authorization != "Bearer anis_ai_access":

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    if not model_ready:

        return {
            "reply": "AI Core still initializing..."
        }

    try:

        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=payload.message,
            config=types.GenerateContentConfig(
                system_instruction="""
                You are ANIS AI SHIELD.
                Give intelligent, helpful, accurate answers.
                Behave like ChatGPT and Gemini combined.
                """
            )
        )

        return {
            "reply": response.text
        }

    except Exception as e:

        logger.error(f"AI ERROR: {e}")

        raise HTTPException(
            status_code=500,
            detail="AI processing failed"
        )

# =========================
# ROOT
# =========================

@app.get("/")
async def root():
    return {
        "message": "ANIS-AI-SHIELD Backend Online"
    }
