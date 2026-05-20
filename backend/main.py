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

# Internal Module Imports (Assumes auth.py and database.py exist in the same directory)
from auth import verify_password, create_access_token, get_current_user
from database import get_user_profile, log_login_event, save_chat_session

# Setup System Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem.Main")

# Track Server Boot Time for Health Checks
SERVER_START_TIME = time.time()

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI Core Application
app = FastAPI(title="ANIS-AI-SHIELD Core", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enterprise CORS Configuration - Explicitly maps all your platform environments
ALLOWED_ORIGINS = [
    "https://anis-ai-shield-gm7f4rats-anisbharadwajs-projects.vercel.app",
    "https://anis-ai-shield-18e1l1kb2-anisbharadwajs-projects.vercel.app",
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

# AI Core Engine Initialization
try:
    # Looks for GEMINI_API_KEY environment variable automatically
    ai_client = genai.Client()
    logger.info("Neural Threat Profiler Engine initialized successfully.")
except Exception as e:
    logger.critical(f"AI Matrix Interface completely offline: {e}")
    ai_client = None

# Hardware challenge dictionary to track standard multi-stage authentication states
PENDING_BIOMETRIC_CHALLENGES = {}

# Pydantic Schemas for JSON Payloads
class ChatQuery(BaseModel):
    message: str
    history: list = []

class BiometricVerifyPayload(BaseModel):
    signature: str
    userEmail: str

# --- SYSTEM ENDPOINTS ---

@app.get("/health")
def health_check():
    """Returns infrastructure operational status and total runtime metrics."""
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
    """Processes stage-one credential validation using application/x-www-form-urlencoded payloads."""
    ip = get_remote_address(request)
    
    # Check signature validation state
    if not captcha_verified:
        log_login_event(username, "BLOCKED_BY_CAPTCHA", ip)
        raise HTTPException(status_code=403, detail="Anti-Bot validation challenge failure.")

    # Match system mapping credentials
    user_record = get_user_profile(username)
    if not user_record:
        log_login_event(username, "USER_NOT_FOUND", ip)
        raise HTTPException(status_code=401, detail="Invalid access credential mappings.")

    # Verify cryptographic password hash match
    if not verify_password(password, user_record.get("hashed_password")):
        log_login_event(username, "INVALID_PASSWORD", ip)
        raise HTTPException(status_code=401, detail="Invalid access credential mappings.")

    log_login_event(username, "STAGE_1_CLEARED", ip, "AI Assessment Passed")
    
    # Generate cryptographic token for the physical verification challenge
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
    """Executes final stage access validation and returns the system authorization context."""
    ip = get_remote_address(request)
    
    if payload.userEmail not in PENDING_BIOMETRIC_CHALLENGES:
        raise HTTPException(status_code=400, detail="Challenge handshake context timed out.")
    
    # Evict used challenge token
    del PENDING_BIOMETRIC_CHALLENGES[payload.userEmail]
    
    log_login_event(payload.userEmail, "SUCCESSFUL_AUTHENTICATION", ip)
    
    # Mint token to initialize communication
    access_token = create_access_token(data={"sub": payload.userEmail})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(request: Request, query: ChatQuery, current_user: str = Depends(get_current_user)):
    """Interfaces with Gemini-2.5-Flash to compute contextual analysis responses without mirroring input."""
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Core processing interface completely offline.")
    
    try:
        contents = []
        
        # Build strict dialogue thread history context
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role, 
                    parts=[types.Part.from_text(text=turn.get("text", ""))]
                )
            )
        
        # Append latest inbound problem evaluation query
        contents.append(
            types.Content(
                role="user", 
                parts=[types.Part.from_text(text=query.message)]
            )
        )

        # Execute processing request via official GenAI API client
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are ANIS-AI-SHIELD, an advanced, highly specialized AI platform terminal "
                    "engineered for secure systems administration, optimization, and real-time analytical evaluation. "
                    "Analyze incoming operator requests deeply and deliver clear, technical solutions with formatted code syntax blocks."
                ),
                temperature=0.3
            )
        )
        
        # Write execution artifact log to database
        save_chat_session(current_user, query.message, response.text)
        
        return {"response": response.text}
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error computing data streams.")
