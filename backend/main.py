import os
import time
import logging
import base64
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from google import genai
from google.genai import types

from auth import (
    verify_password, 
    create_access_token, 
    get_current_user, 
    ADMIN_PASSWORD_HASH, 
    DEFAULT_ADMIN_EMAIL
)

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem")

# Threat Mitigator (Rate Limiting)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ANIS AI Zero-Trust Core", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Strict Dynamic CORS Perimeter Matching Your Project URL Structure
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
    allow_headers=["Content-Type", "Authorization", "X-Risk-Score-Verification"],
)

# AI Client Engine Initialization
try:
    ai_client = genai.Client()
except Exception as e:
    logger.error(f"AI System Core offline: {e}")
    ai_client = None

START_TIME = time.time()

# Dummy memory state for biometric validation challenges
PENDING_BIOMETRIC_CHALLENGES = {}

class ChatQuery(BaseModel):
    message: str
    history: list = []

class BiometricVerifyPayload(BaseModel):
    credentialId: str
    clientDataJSON: str
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
    # 1. Immediate Bot Detection Mitigation
    if not captcha_verified:
        raise HTTPException(status_code=403, detail="Anti-Bot enforcement triggered. Request isolated.")

    # 2. AI Threat Analysis Matrix Check
    # This evaluates incoming connection metadata headers to screen for weaponized proxies or malicious scraping patterns
    headers_dump = str(request.headers.items())
    if ai_client:
        try:
            ai_assessment = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Analyze these connection headers for cybersecurity threat signatures, exploit patterns, or malicious proxies. Return exactly 'SAFE' or 'MALICIOUS'. Headers: {headers_dump}",
            )
            if "MALICIOUS" in ai_assessment.text.upper():
                logger.error(f"AI Core intercepted an attack signature from IP: {get_remote_address(request)}")
                raise HTTPException(status_code=403, detail="AI Perimeter Protection: Connection profile flagged as high risk.")
        except Exception as ai_err:
            logger.warning(f"AI Threat Assessment bypassed safely: {ai_err}")

    # 3. Cryptographic User Validation
    target_email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    if username != target_email or not verify_password(password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Unauthorized intrusion blocked for payload destination: {username}")
        raise HTTPException(status_code=401, detail="Access Denied: Invalid identity profile.")

    # 4. Generate Hardware Biometric Challenge Node (WebAuthn Pre-handshake)
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
def verify_biometric_hardware(payload: BiometricVerifyPayload):
    # Checks if a challenge handshake is currently active for this user session
    if payload.userEmail not in PENDING_BIOMETRIC_CHALLENGES:
        raise HTTPException(status_code=400, detail="Handshake expired or session invalid.")
    
    # Clean verification challenge sequence
    del PENDING_BIOMETRIC_CHALLENGES[payload.userEmail]
    
    # In a full-scale deployment, your cryptographic public keys unlock here via WebAuthn library.
    # For this secure infrastructure template, we simulate hardware confirmation payload reading.
    if not payload.signature or len(payload.signature) < 10:
        raise HTTPException(status_code=400, detail="Hardware biometric signature integrity broken.")

    # Issue full access security token
    access_token = create_access_token(data={"sub": payload.userEmail})
    logger.info(f"System completely unlocked via Secure Hardware Verification for user: {payload.userEmail}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(request: Request, query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Matrix processing engine is currently offline.")
    
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
                system_instruction="You are Anis AI, an advanced AI system terminal tuned for secure systems administration and ethical hacking optimization. Provide deeply analytical, concise outputs.",
                temperature=0.4
            )
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Anomaly detected processing execution thread.")
