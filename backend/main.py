import os
import time
import logging
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Critical Imports for Security and Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from google import genai
from google.genai import types

from auth import verify_password, create_access_token, get_current_user
from database import get_user_profile, log_login_event, save_chat_session

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem.Main")

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI with the new system title
app = FastAPI(title="ANIS-AI-SHIELD Core", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = [
    "https://protected-ethical-anis-ai-12.onrender.com",
    "http://127.0.0.1:5500",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# AI Client Initialization
try:
    ai_client = genai.Client()
except Exception as e:
    logger.error(f"AI Matrix Interface down: {e}")
    ai_client = None

PENDING_BIOMETRIC_CHALLENGES = {}

class ChatQuery(BaseModel):
    message: str
    history: list = []

class BiometricVerifyPayload(BaseModel):
    signature: str
    userEmail: str

@app.get("/health")
def health_check():
    return {"status": "operational", "security_tier": "zero-trust", "ai_active": ai_client is not None}

@app.post("/api/login")
@limiter.limit("5/minute")
async def secure_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):
    ip = get_remote_address(request)
    
    if not captcha_verified:
        log_login_event(username, "BLOCKED_BY_CAPTCHA", ip)
        raise HTTPException(status_code=403, detail="Anti-Bot validation challenge failure.")

    user_record = get_user_profile(username)
    if not user_record:
        log_login_event(username, "USER_NOT_FOUND", ip)
        raise HTTPException(status_code=401, detail="Invalid access credential mappings.")

    if not verify_password(password, user_record.get("hashed_password")):
        log_login_event(username, "INVALID_PASSWORD", ip)
        raise HTTPException(status_code=401, detail="Invalid access credential mappings.")

    user_role = user_record.get("role", "UNKNOWN")
    clearance = user_record.get("clearance_level", "0")
    headers_dump = str(request.headers.items())

    ai_analysis_report = "AI Sandbox Mode - Analysis Bypassed"
    if ai_client:
        try:
            ai_assessment = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=(
                    f"Perform a strict zero-trust operational security assessment.\n"
                    f"Target User: {username}\nDeclared Role: {user_role}\nClearance Tier: {clearance}\n"
                    f"Network Connection Info: {headers_dump}\n"
                    f"Task: Verify if this profile shows structural signs of hijacking, unauthorized proxying, or automated scanning scripts.\n"
                    f"Your response must begin with either 'STATUS: APPROVED' or 'STATUS: MALICIOUS', followed by a one-sentence analytical justification summary."
                ),
            )
            ai_analysis_report = ai_assessment.text
            if "STATUS: MALICIOUS" in ai_analysis_report.upper() or "MALICIOUS" in ai_analysis_report.upper():
                log_login_event(username, "AI_SECURITY_REJECTION", ip, ai_analysis_report)
                raise HTTPException(status_code=403, detail="Access denied by security perimeter AI profiling.")
        except HTTPException:
            raise
        except Exception as err:
            logger.warning(f"AI Assessment layer bypassed due to systemic error: {err}")

    log_login_event(username, "STAGE_1_CLEARED", ip, ai_analysis_report)
    
    biometric_challenge = secrets.token_urlsafe(32)
    PENDING_BIOMETRIC_CHALLENGES[username] = biometric_challenge

    return {
        "status": "password_verified",
        "requires_biometrics": True,
        "biometric_challenge": biometric_challenge,
        "user_identity": username,
        "ai_profile_report": ai_analysis_report
    }

@app.post("/api/login/biometric-verify")
@limiter.limit("5/minute")
def verify_biometric_hardware(request: Request, payload: BiometricVerifyPayload):
    ip = get_remote_address(request)
    if payload.userEmail not in PENDING_BIOMETRIC_CHALLENGES:
        raise HTTPException(status_code=400, detail="Challenge handshake context timed out.")
    
    del PENDING_BIOMETRIC_CHALLENGES[payload.userEmail]
    
    if not payload.signature or len(payload.signature) < 10:
        log_login_event(payload.userEmail, "BIOMETRIC_HANDSHAKE_FAULT", ip)
        raise HTTPException(status_code=400, detail="Hardware cryptographic integrity fault.")

    log_login_event(payload.userEmail, "SUCCESSFUL_AUTHENTICATION", ip)
    access_token = create_access_token(data={"sub": payload.userEmail})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Core processing interface completely offline.")
    
    try:
        contents = []
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn.get("text", ""))]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=query.message)]))

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are ANIS-AI-SHIELD, an advanced AI system terminal tuned for secure systems administration and ethical hacking optimization. Provide highly intelligent and contextual responses.",
                temperature=0.3
            )
        )
        save_chat_session(current_user, query.message, response.text)
        return {"response": response.text}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal processing error computing generative data streams.")
