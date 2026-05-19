import os
import time
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Initialize System Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnisAISystem")

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ANIS AI Secure System Backend", version="2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Security Setup
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "[http://127.0.0.1:5500](http://127.0.0.1:5500)",
    "[https://protected-ethical-anis-ai.vercel.app](https://protected-ethical-anis-ai.vercel.app)", # Replace with your actual Vercel URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten down to ALLOWED_ORIGINS after confirming Vercel production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client
# It automatically picks up the GEMINI_API_KEY environment variable
try:
    ai_client = genai.Client()
except Exception as e:
    logger.error(f"Failed to initialize Gemini Client: {e}")
    ai_client = None

# Track System Startup for Uptime
START_TIME = time.time()

# Request Schemas
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
    # Automated Bot/Captcha Check Assertion
    if not captcha_verified:
        raise HTTPException(status_code=400, detail="Bot activity detected. Anti-hacker human verification failed.")
    
    target_email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    
    # Secure Time-Constant-Like Validation Check
    if username != target_email or not verify_password(password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Unauthorized access attempt detected on username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied. Invalid Admin Credentials or Token."
        )
    
    access_token = create_access_token(data={"sub": username})
    logger.info(f"Admin successfully authenticated: {username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(request: Request, query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Service currently offline or API key missing.")
    
    # Input validation / Cross-Site Scripting (XSS) basic mitigation
    sanitized_input = query.message.replace("<script>", "").replace("</script>", "").strip()
    if not sanitized_input:
        raise HTTPException(status_code=400, detail="Empty transmission payload detected.")

    try:
        # Reconstruct chat memory context for the Gemini SDK
        contents = []
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=turn.get("text", ""))]
            ))
        
        # Append the current fresh message
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=sanitized_input)]))

        # Request intelligence output from gemini-2.5-flash
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are Anis AI, an advanced cyber security intelligence core. Give expert, direct answers. Do not mirror back what the user says.",
                max_output_tokens=800,
                temperature=0.7
            )
        )
        
        return {"response": response.text}
    except Exception as e:
        logger.error(f"GenAI Core Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred within the AI Generation Engine.")
