import os
import time
import logging
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

# Core Logging Infrastructure
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem")

# Anti-DDoS Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ANIS AI Secure System Backend", version="2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure Cross-Origin Resource Sharing (CORS) Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows smooth testing across both dynamic Vercel previews & production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Google Gemini Client Core
try:
    # Google's official modern SDK automatically reads the GEMINI_API_KEY environment variable
    ai_client = genai.Client()
except Exception as e:
    logger.error(f"Failed to initialize Gemini Client engine: {e}")
    ai_client = None

START_TIME = time.time()

class ChatQuery(BaseModel):
    message: str
    history: list = []

@app.get("/health")
@limiter.limit("20/minute")
def health_check(request: Request):
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "status": "ok",
        "uptime": f"{uptime_seconds}s",
        "version": "2.0",
        "security": "active",
        "ai_connected": ai_client is not None
    }

@app.post("/api/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):
    if not captcha_verified:
        raise HTTPException(status_code=400, detail="Perimeter Breach: Anti-Bot validation failed.")
    
    target_email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    
    if username != target_email or not verify_password(password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Unauthorized intrusion blocked for identity: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: Invalid cryptographic token signature."
        )
    
    access_token = create_access_token(data={"sub": username})
    logger.info(f"Root authorization node unlocked for: {username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(request: Request, query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Processing Array is offline. Validate GEMINI_API_KEY variable configuration.")
    
    # Input Sanitization against basic HTML injection
    sanitized_input = query.message.replace("<script>", "").replace("</script>", "").strip()
    if not sanitized_input:
        raise HTTPException(status_code=400, detail="Null payload transmission intercepted.")

    try:
        # Re-compile context history structural maps
        contents = []
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=turn.get("text", ""))]
            ))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=sanitized_input)]))

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are Anis AI, a highly intelligent cybersecurity core terminal assistant. Provide contextual responses. Do not echo or parrot the user input back to them.",
                max_output_tokens=1000,
                temperature=0.7
            )
        )
        
        return {"response": response.text}
    except Exception as e:
        logger.error(f"GenAI Core Generation Exception: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal anomaly processing logic sequence.")
