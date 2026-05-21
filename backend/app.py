import os
import time
import logging
from fastapi import FastAPI, Depends, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.generativeai as genai

from backend.database import engine, get_db, init_db, User
from backend.auth import verify_password, create_access_token, decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Anis-AI-Core")

SERVER_START_TIME = time.time()
init_db() # Create tables and seed users on startup

app = FastAPI(title="Anis-AI-Shield", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://anis-ai-shield-hrz0hohhq-anisbharadwajs-projects.vercel.app",
        "https://anis-ai-shield.vercel.app",
        "http://localhost:5500", "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.error("MISSING GEMINI API KEY")

class ChatPayload(BaseModel):
    message: str
    history: list = [] # Allows frontend to send memory

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "uptime": int(time.time() - SERVER_START_TIME),
        "version": "3.0.0",
        "ai_connected": bool(GEMINI_API_KEY)
    }

@app.post("/api/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha_verified: bool = Form(...),
    db: Session = Depends(get_db)
):
    if not captcha_verified:
        raise HTTPException(status_code=400, detail="Human verification required.")
    
    user = db.query(User).filter(User.render_url == username).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt: {username}")
        raise HTTPException(status_code=401, detail="Invalid Render URL or Password")
    
    token = create_access_token(data={"sub": user.render_url})
    return {"access_token": token, "token_type": "bearer", "user": username}

@app.post("/api/chat")
def chat_with_ai(payload: ChatPayload, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")

    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="AI Core Offline")

    try:
        # Format history for Gemini
        formatted_history = []
        for msg in payload.history:
            formatted_history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })
        
        chat = ai_model.start_chat(history=formatted_history)
        response = chat.send_message(payload.message)
        return {"reply": response.text}
    except Exception as e:
        logger.error(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="AI processing failure")
