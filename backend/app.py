import os
import json
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Form, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from google import genai
from google.genai import types

from database import SessionLocal, User, ChatMessage, init_db
from auth import hash_password, verify_password, create_access_token, decode_token

APP_NAME = "ANIS-AI-SHIELD"
APP_VERSION = "3.0.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(APP_NAME)

SERVER_START_TIME = time.time()

SECRET_KEY = os.getenv("SECRET_KEY", "anis_ai_secret_key_2026")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"

ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "").strip()
if ALLOWED_ORIGINS_RAW:
    ALLOWED_ORIGINS = [x.strip() for x in ALLOWED_ORIGINS_RAW.split(",") if x.strip()]
else:
    ALLOWED_ORIGINS = [
        os.getenv("VERCEL_URL", "https://anis-ai-shield.vercel.app"),
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

INITIAL_USERS_RAW = os.getenv("INITIAL_USERS", "").strip()

SYSTEM_PROMPT = """
You are Anis AI Shield.

You are the intelligent assistant for ANIS-AI-SHIELD.

Rules:
- Answer clearly, naturally, and professionally.
- Help with coding, AI, FastAPI, Render, Vercel, Gemini, cybersecurity, deployment, and web apps.
- Never repeat the user's message as the final answer.
- Do not expose secrets, tokens, passwords, or private backend details.
- Use context from previous messages when available.
"""

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

_ai_client = None
_ai_initialized = False


def get_ai_client():
    global _ai_client, _ai_initialized

    if _ai_client is not None:
        return _ai_client

    if not GEMINI_API_KEY:
        return None

    try:
        _ai_client = genai.Client(api_key=GEMINI_API_KEY)
        _ai_initialized = True
        logger.info("Gemini AI Connected")
        return _ai_client
    except Exception as e:
        logger.error(f"Gemini Initialization Error: {e}")
        return None


def get_token_from_request(request: Request, authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("anis_token")
    if cookie_token:
        return cookie_token

    return None


def seed_users():
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if existing:
            return

        users_to_seed = []

        if INITIAL_USERS_RAW:
            try:
                users_to_seed = json.loads(INITIAL_USERS_RAW)
                if not isinstance(users_to_seed, list):
                    users_to_seed = []
            except Exception as e:
                logger.error(f"INITIAL_USERS parse error: {e}")
                users_to_seed = []

        if not users_to_seed:
            admin_username = os.getenv("ADMIN_USERNAME", "").strip()
            admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
            admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()

            if admin_username:
                if admin_password_hash:
                    users_to_seed = [{
                        "url": admin_username,
                        "pass_hash": admin_password_hash
                    }]
                elif admin_password:
                    users_to_seed = [{
                        "url": admin_username,
                        "pass": admin_password
                    }]

        for item in users_to_seed:
            username = str(item.get("url", "")).strip()
            if not username:
                continue

            if item.get("pass_hash"):
                password_hash = str(item["pass_hash"]).strip()
            else:
                plain = str(item.get("pass", "")).strip()
                if not plain:
                    continue
                password_hash = hash_password(plain)

            db.add(User(
                username=username,
                password_hash=password_hash,
                is_active=True,
            ))

        db.commit()
        logger.info("Initial users seeded")
    except Exception as e:
        db.rollback()
        logger.error(f"Seed users error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_users()
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


def build_prompt(db, username: str, message: str) -> str:
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.username == username)
        .order_by(ChatMessage.id.desc())
        .limit(8)
        .all()
    )
    history = list(reversed(history))

    prompt_lines = [SYSTEM_PROMPT.strip(), "", "Conversation context:"]
    for row in history:
        prompt_lines.append(f"{row.role.capitalize()}: {row.content}")

    prompt_lines.extend([
        f"User: {message}",
        "Assistant:"
    ])

    return "\n".join(prompt_lines)


def save_chat_turn(db, username: str, user_text: str, assistant_text: str):
    db.add(ChatMessage(username=username, role="user", content=user_text))
    db.add(ChatMessage(username=username, role="assistant", content=assistant_text))
    db.commit()


@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
    }


@app.get("/ready")
async def ready():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - SERVER_START_TIME),
        "version": APP_VERSION,
        "ai_initialized": bool(_ai_client),
        "ai_connected": bool(GEMINI_API_KEY),
        "server": APP_NAME,
    }


@app.post("/api/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...),
):
    if not captcha_verified:
        raise HTTPException(status_code=403, detail="Human verification required.")

    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.username == username, User.is_active == True)  # noqa: E712
            .first()
        )

        if not user:
            logger.warning(f"Invalid login username: {username}")
            raise HTTPException(status_code=401, detail="Invalid Render URL or password.")

        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid password attempt: {username}")
            raise HTTPException(status_code=401, detail="Invalid Render URL or password.")

        token = create_access_token({
            "sub": user.username,
            "username": user.username,
            "role": "admin",
        })

        response = JSONResponse({
            "success": True,
            "message": "Authentication successful",
            "access_token": token,
        })

        response.set_cookie(
            key="anis_token",
            value=token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        logger.info(f"Login success: {username}")
        return response

    finally:
        db.close()


@app.post("/api/logout")
async def logout():
    response = JSONResponse({"success": True, "message": "Logged out"})
    response.delete_cookie("anis_token", path="/")
    return response


def verify_request_token(request: Request, authorization: Optional[str]) -> dict:
    token = get_token_from_request(request, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization missing.")

    decoded = decode_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Session expired.")

    return decoded


def generate_ai_reply(username: str, message: str) -> str:
    client = get_ai_client()
    if not client:
        raise HTTPException(status_code=503, detail="AI Core offline.")

    db = SessionLocal()
    try:
        prompt = build_prompt(db, username, message)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )

        reply = getattr(response, "text", None) or "No response returned."
        save_chat_turn(db, username, message, reply)
        return reply

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="AI processing failed.")
    finally:
        db.close()


@app.post("/api/chat")
async def chat(
    request: Request,
    payload: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    decoded = verify_request_token(request, authorization)
    username = decoded.get("username") or decoded.get("sub") or "unknown"
    reply = generate_ai_reply(username=username, message=payload.message)
    return {"reply": reply}


@app.post("/api/chat/stream")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    decoded = verify_request_token(request, authorization)
    username = decoded.get("username") or decoded.get("sub") or "unknown"

    client = get_ai_client()
    if not client:
        raise HTTPException(status_code=503, detail="AI Core offline.")

    db = SessionLocal()
    prompt = build_prompt(db, username, payload.message)
    db.close()

    def event_stream():
        full_text = []
        try:
            stream = client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )

            for chunk in stream:
                text = getattr(chunk, "text", "") or ""
                if text:
                    full_text.append(text)
                    yield f"data: {json.dumps({'type': 'chunk', 'text': text}, ensure_ascii=False)}\n\n"

            final_reply = "".join(full_text).strip() or "No response returned."

            db2 = SessionLocal()
            try:
                save_chat_turn(db2, username, payload.message, final_reply)
            finally:
                db2.close()

            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Streaming AI Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'AI processing failed.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
