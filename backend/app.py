import os
import time
import logging

from fastapi import FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jose import jwt, JWTError
from passlib.context import CryptContext

from google import genai
from google.genai import types

# =========================================
# LOGGING CONFIG
# =========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ANIS-AI-SHIELD")

# =========================================
# ENVIRONMENT VARIABLES
# =========================================
SECRET_KEY = os.getenv("SECRET_KEY", "anis_ultra_secure_key")

ALGORITHM = "HS256"

# LOGIN USERNAME = YOUR RENDER URL
ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "https://protected-ethical-anis-ai-12.onrender.com"
)

# PASSWORD
ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "AnisSecure2026"
)

# GEMINI API KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# FRONTEND URL
VERCEL_URL = os.getenv(
    "VERCEL_URL",
    "https://anis-ai-shield.vercel.app"
)

# =========================================
# GEMINI AI CONFIG
# =========================================
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Gemini AI Connected")
except Exception as e:
    logger.error(f"Gemini AI Failed: {e}")

# =========================================
# FASTAPI INIT
# =========================================
app = FastAPI(
    title="ANIS-AI-SHIELD",
    version="3.0.0"
)

SERVER_START_TIME = time.time()

# =========================================
# PASSWORD HASHING
# =========================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

hashed_password = pwd_context.hash(ADMIN_PASSWORD)

# =========================================
# CORS SECURITY
# =========================================
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

# =========================================
# REQUEST MODEL
# =========================================
class ChatRequest(BaseModel):
    message: str

# =========================================
# JWT TOKEN CREATE
# =========================================
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# =========================================
# VERIFY JWT TOKEN
# =========================================
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

# =========================================
# ROOT ROUTE
# =========================================
@app.get("/")
def root():
    return {
        "message": "ANIS-AI-SHIELD Backend Running"
    }

# =========================================
# HEALTH CHECK
# =========================================
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "uptime": int(time.time() - SERVER_START_TIME),
        "version": "3.0.0",
        "ai_connected": bool(GEMINI_API_KEY)
    }

# =========================================
# LOGIN API
# =========================================
@app.post("/api/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...)
):

    # HUMAN VERIFY
    if not captcha_verified:
        raise HTTPException(
            status_code=403,
            detail="Human verification required."
        )

    # CHECK USERNAME
    if username != ADMIN_USERNAME:
        logger.warning(f"Invalid username attempt: {username}")

        raise HTTPException(
            status_code=401,
            detail="Invalid Render URL."
        )

    # VERIFY PASSWORD
    if not pwd_context.verify(password, hashed_password):
        logger.warning("Invalid password attempt")

        raise HTTPException(
            status_code=401,
            detail="Invalid password."
        )

    # CREATE JWT TOKEN
    token = create_access_token({
        "sub": username,
        "role": "admin"
    })

    logger.info(f"Successful login: {username}")

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# =========================================
# AI CHAT API
# =========================================
@app.post("/api/chat")
async def ai_chat(
    request: ChatRequest,
    authorization: str = Header(None)
):

    # CHECK TOKEN
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization missing."
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid token format."
        )

    token = authorization.split(" ")[1]

    # VERIFY TOKEN
    decoded = verify_token(token)

    if not decoded:
        raise HTTPException(
            status_code=401,
            detail="Session expired."
        )

    # CHECK API KEY
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key missing."
        )

    try:

        SYSTEM_PROMPT = """
You are Anis AI Shield.

You are an advanced AI assistant for the ANIS-AI-SHIELD platform.

Rules:
- Answer clearly and professionally.
- Help users about AI, coding, cybersecurity, web apps, deployment, Render, Vercel, Python, FastAPI, Gemini AI, and technology.
- Never reveal secret keys or backend secrets.
- Keep responses intelligent and accurate.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )

        return {
            "reply": response.text
        }

    except Exception as e:

        logger.error(f"AI ERROR: {e}")

        raise HTTPException(
            status_code=500,
            detail="AI processing failed."
        )

# =========================================
# START SERVER
# =========================================
if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=port
    )
