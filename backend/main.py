import os
import time
import logging
import secrets
from fastapi import FastAPI, Depends, HTTPException, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Security and Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Google GenAI SDK
from google import genai
from google.genai import types

# System Authorization Utility (Imported from auth.py)
from auth import create_access_token, get_current_user

# Setup System Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem.Main")

SERVER_START_TIME = time.time()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="ANIS-AI-SHIELD Core", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# FIXED: Direct browser permission whitelist to eliminate "Failed to fetch" CORS blocks
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

try:
    ai_client = genai.Client()
    logger.info("Neural Threat Profiler Engine initialized successfully.")
except Exception as e:
    logger.critical(f"AI Matrix Interface offline: {e}")
    ai_client = None

PENDING_BIOMETRIC_CHALLENGES = {}

# Operator Credentials
VALID_OPERATOR_IDENTITY = "https://protected-ethical-anis-ai-12.onrender.com"  
VALID_OPERATOR_PASSPHRASE = "AN1IS2H3"                                         

class ChatQuery(BaseModel):
    message: str
    history: list = []

class BiometricVerifyPayload(BaseModel):
    signature: str
    userEmail: str

@app.get("/health")
def health_check():
    uptime_seconds = int(time.time() - SERVER_START_TIME)
    return {
        "status": "ok",
        "uptime": uptime_seconds,
        "version": "2.0",
        "ai_connected": ai_client is not None
    }

@app.post("/api/login")
@limiter.limit("5/minute")
async def secure_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):
    if not captcha_verified:
        raise HTTPException(status_code=403, detail="Anti-Bot validation challenge failure.")

    if username != VALID_OPERATOR_IDENTITY or password != VALID_OPERATOR_PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid access credential mappings.")

    logger.info(f"Operator Stage 1 Cleared for identity: {username}")
    
    biometric_challenge = secrets.token_urlsafe(32)
    PENDING_BIOMETRIC_CHALLENGES[username] = biometric_challenge

    return {
        "status": "password_verified",
        "requires_biometrics": True,
        "biometric_challenge": biometric_challenge,
        "user_identity": username
    }

@app.post("/api/login/biometric-verify")
@limiter.limit("5/minute")
def verify_biometric_hardware(request: Request, payload: BiometricVerifyPayload):
    if payload.userEmail not in PENDING_BIOMETRIC_CHALLENGES:
        raise HTTPException(status_code=400, detail="Challenge handshake context timed out.")
    
    del PENDING_BIOMETRIC_CHALLENGES[payload.userEmail]
    
    access_token = create_access_token(data={"sub": payload.userEmail})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(request: Request, query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Core processing interface offline.")
    
    try:
        contents = []
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=turn.get("text", ""))] )
            )
        
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=query.message)])
        )

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are ANIS-AI-SHIELD, an advanced, highly specialized AI platform terminal "
                    "engineered for secure systems administration. Analyze incoming requests deeply "
                    "and deliver clear, technical solutions with formatted code blocks."
                ),
                temperature=0.3
            )
        )
        return {"response": response.text}
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error computing data streams.")
