import os
import time
import logging
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError

from google import genai
from google.genai import types

# =========================================================
# ANIS-AI-SHIELD BACKEND CORE
# =========================================================

APP_NAME = "ANIS-AI-SHIELD"
APP_VERSION = "3.0.0"

# =========================================================
# LOGGING SYSTEM
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(APP_NAME)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "anis_ai_ultra_secret_key_change_this"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LOGIN USERNAME = YOUR RENDER URL
ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "https://protected-ethical-anis-ai-12.onrender.com"
)

# PASSWORD = CHANGE THIS HASH IN RENDER ENVIRONMENT
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq"
)

SERVER_START_TIME = time.time()

# =========================================================
# PASSWORD HASHING
# =========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# =========================================================
# GEMINI AI CLIENT
# =========================================================

ai_client = None

try:
    if GEMINI_API_KEY:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini AI Connected")
    else:
        logger.warning("Gemini API Key Missing")
except Exception as e:
    logger.error(f"AI Initialization Error: {e}")

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)

# =========================================================
# CORS SECURITY
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://anis-ai-shield.vercel.app",
        "https://protected-ethical-anis-ai-12.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str

# =========================================================
# JWT TOKEN FUNCTIONS
# =========================================================

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None

# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "online"
    }

# =========================================================
# HEALTH ENDPOINT
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - SERVER_START_TIME),
        "version": APP_VERSION,
        "ai_connected": bool(GEMINI_API_KEY),
        "server": APP_NAME
    }

# =========================================================
# LOGIN ENDPOINT
# =========================================================

@app.post("/api/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):

    # HUMAN VERIFICATION
    if not captcha_verified:
        logger.warning("Captcha verification failed")

        raise HTTPException(
            status_code=403,
            detail="Human verification required"
        )

    # USERNAME CHECK
    if username != ADMIN_USERNAME:
        logger.warning(f"Invalid username: {username}")

        raise HTTPException(
            status_code=401,
            detail="Invalid Render URL"
        )

    # PASSWORD CHECK
    password_valid = pwd_context.verify(
        password,
        ADMIN_PASSWORD_HASH
    )

    if not password_valid:
        logger.warning("Invalid password attempt")

        raise HTTPException(
            status_code=401,
            detail="Invalid Password"
        )

    # CREATE TOKEN
    access_token = create_access_token(
        {
            "sub": username,
            "role": "admin"
        }
    )

    logger.info(f"Successful login: {username}")

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Authentication successful"
    }

# =========================================================
# AI CHAT ENDPOINT
# =========================================================

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(None)
):

    # TOKEN CHECK
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization missing"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    token = authorization.split(" ")[1]

    user = verify_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired"
        )

    # AI CHECK
    if not ai_client:
        raise HTTPException(
            status_code=500,
            detail="Gemini AI not connected"
        )

    try:

        system_prompt = """
        You are Anis AI Shield Assistant.

        Rules:
        - Give professional answers.
        - Help users about coding, AI, cybersecurity, deployment,
          websites, and technology.
        - Be fast and clear.
        - Never expose secrets or tokens.
        - Keep responses clean and intelligent.
        """

        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        return {
            "reply": response.text
        }

    except Exception as e:

        logger.error(f"AI Error: {e}")

        raise HTTPException(
            status_code=500,
            detail="AI processing failed"
        )

# =========================================================
# STARTUP EVENT
# =========================================================

@app.on_event("startup")
async def startup_event():
    logger.info(f"{APP_NAME} Backend Started")

# =========================================================
# SHUTDOWN EVENT
# =========================================================

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{APP_NAME} Backend Shutdown")

# =========================================================
# MAIN SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
