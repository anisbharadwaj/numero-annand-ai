import os
import time
import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Form,
    Header
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from google import genai
from google.genai import types

from backend.database import find_user
from backend.auth import (
    create_access_token,
    decode_token
)

# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("ANIS-AI-SHIELD")

# ---------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        logger.info("Gemini AI Connected")

    except Exception as e:
        logger.error(f"Gemini Init Error: {e}")

# ---------------------------------------------------
# APP
# ---------------------------------------------------

app = FastAPI(
    title="Anis-AI-Shield",
    version="3.0.0"
)

SERVER_START_TIME = time.time()

# ---------------------------------------------------
# CORS
# ---------------------------------------------------

VERCEL_URL = os.getenv(
    "VERCEL_URL",
    "https://anis-ai-shield.vercel.app"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        VERCEL_URL,
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# MODELS
# ---------------------------------------------------

class ChatRequest(BaseModel):
    message: str

# ---------------------------------------------------
# HEALTH
# ---------------------------------------------------

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "uptime": int(time.time() - SERVER_START_TIME),
        "version": "3.0.0",
        "ai_connected": bool(client)
    }

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.post("/api/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):

    if not captcha_verified:
        raise HTTPException(
            status_code=403,
            detail="Human verification required."
        )

    user = find_user(username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Render URL."
        )

    if user["pass"] != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password."
        )

    token = create_access_token({
        "sub": username
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ---------------------------------------------------
# CHAT
# ---------------------------------------------------

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(None)
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization missing"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    token = authorization.split(" ")[1]

    decoded = decode_token(token)

    if not decoded:
        raise HTTPException(
            status_code=401,
            detail="Session expired"
        )

    if not client:
        return {
            "reply": "AI Core Offline. Gemini API key missing."
        }

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=request.message,

            config=types.GenerateContentConfig(
                system_instruction="""
You are Anis AI.
You are the intelligent AI assistant of Anis-AI-Shield.

Rules:
- Give clear answers
- Help users properly
- Explain website features
- Explain dashboard
- Explain memberships
- Explain security
- Explain login system
- Be professional
- Be intelligent
- Never say connection severed
- Always answer naturally
"""
            )
        )

        return {
            "reply": response.text
        }

    except Exception as e:

        logger.error(f"Gemini Error: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"AI processing failed: {str(e)}"
        )
