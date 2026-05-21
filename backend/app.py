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

# ==================================================
# APP CONFIG
# ==================================================

APP_NAME = "ANIS-AI-SHIELD"
APP_VERSION = "3.0.0"

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(APP_NAME)

# ==================================================
# ENV VARIABLES
# ==================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "anis_ai_secret_key_2026"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 1440

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "https://protected-ethical-anis-ai-12.onrender.com"
)

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    "$2b$12$2M5QYz9VYxY5X0N4V3nP7eJ8x4Q9zB8W6m9xQ8Y0tB0bM3f3mJm9K"
)

SERVER_START_TIME = time.time()

# ==================================================
# PASSWORD HASHER
# ==================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ==================================================
# GEMINI AI CLIENT
# ==================================================

ai_client = None

try:
    if GEMINI_API_KEY:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini AI Connected")
    else:
        logger.warning("Gemini API Key Missing")
except Exception as e:
    logger.error(f"Gemini Initialization Error: {e}")

# ==================================================
# FASTAPI
# ==================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# REQUEST MODEL
# ==================================================

class ChatRequest(BaseModel):
    message: str

# ==================================================
# TOKEN FUNCTIONS
# ==================================================

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

# ==================================================
# ROOT
# ==================================================

@app.get("/")
async def root():

    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "online"
    }

# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "uptime": round(time.time() - SERVER_START_TIME),
        "version": APP_VERSION,
        "ai_connected": bool(GEMINI_API_KEY)
    }

# ==================================================
# LOGIN
# ==================================================

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

    valid_password = pwd_context.verify(
        password,
        ADMIN_PASSWORD_HASH
    )

    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid Password"
        )

    access_token = create_access_token(
        {
            "sub": username,
            "role": "admin"
        }
    )

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer"
    }

# ==================================================
# AI CHAT
# ==================================================

@app.post("/api/chat")
async def ai_chat(
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
            detail="Invalid authorization format"
        )

    token = authorization.split(" ")[1]

    user = verify_token(token)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Session expired"
        )

    if not ai_client:

        raise HTTPException(
            status_code=500,
            detail="Gemini AI not connected"
        )

    try:

        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction="""
                You are Anis AI Shield.
                Help users professionally.
                Answer coding, AI, deployment,
                cybersecurity and tech questions.
                """
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

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=port
    )
