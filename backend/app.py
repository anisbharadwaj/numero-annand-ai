import os
import time
import logging
from fastapi import FastAPI, Depends, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.generativeai as genai

from backend.database import engine, get_db, init_db, User, pwd_context
from backend.auth import create_access_token, decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Anis-AI-API")

SERVER_START = time.time()
app = FastAPI(title="Anis-AI-Shield")

# Enable CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Accepts all origins to prevent Fetch Errors
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# Setup AI
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    sys_prompt = """You are Anis AI, the core intelligence of the Anis-AI-Shield platform.
    Your duties: Assist the user with cybersecurity, analyze inputs, and explain the platform.
    The platform uses a Render URL + Password login, followed by biometric Passkey 2FA.
    Access to you requires an active Monthly (₹200) or Yearly (₹1200) membership paid via QR code.
    Keep answers concise, highly intelligent, use markdown, and be helpful."""
    ai_model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=sys_prompt)

# Pydantic Models
class ChatPayload(BaseModel):
    message: str
    history: list = []

class BiometricPayload(BaseModel):
    credential_id: str

# Endpoints
@app.get("/health")
def health():
    return {
        "status": "ok", 
        "uptime": int(time.time() - SERVER_START),
        "version": "4.0.0-Production",
        "ai_connected": bool(GEMINI_KEY)
    }

@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...), human_check: bool = Form(...), db: Session = Depends(get_db)):
    if not human_check:
        raise HTTPException(status_code=400, detail="Human verification required")
    
    user = db.query(User).filter(User.render_url == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    token = create_access_token(data={"sub": user.render_url, "step": "password_cleared"})
    return {
        "access_token": token, 
        "biometric_enabled": user.biometric_enabled,
        "membership_tier": user.membership_tier,
        "membership_active": user.membership_active
    }

@app.post("/api/biometrics/register")
def register_biometric(payload: BiometricPayload, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_data = decode_token(authorization.split(" ")[1]) if authorization else None
    if not user_data: raise HTTPException(status_code=401)
    
    user = db.query(User).filter(User.render_url == user_data["sub"]).first()
    user.biometric_enabled = True
    user.webauthn_credential_id = payload.credential_id
    db.commit()
    
    full_token = create_access_token(data={"sub": user.render_url, "step": "fully_authenticated"})
    return {"access_token": full_token, "status": "Biometrics Secured"}

@app.post("/api/biometrics/verify")
def verify_biometric(payload: BiometricPayload, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_data = decode_token(authorization.split(" ")[1]) if authorization else None
    if not user_data: raise HTTPException(status_code=401)
    
    user = db.query(User).filter(User.render_url == user_data["sub"]).first()
    if user.webauthn_credential_id != payload.credential_id:
        raise HTTPException(status_code=403, detail="Biometric Mismatch. Intruder detected.")
        
    full_token = create_access_token(data={"sub": user.render_url, "step": "fully_authenticated"})
    return {"access_token": full_token}

@app.post("/api/membership/upgrade")
def upgrade_membership(plan: str = Form(...), authorization: str = Header(None), db: Session = Depends(get_db)):
    user_data = decode_token(authorization.split(" ")[1]) if authorization else None
    if not user_data: raise HTTPException(status_code=401)
    
    user = db.query(User).filter(User.render_url == user_data["sub"]).first()
    user.membership_tier = plan
    user.membership_active = True 
    db.commit()
    return {"status": "Membership Upgraded"}

@app.post("/api/chat")
def chat(payload: ChatPayload, authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization: raise HTTPException(status_code=401, detail="No Auth Token")
    token_data = decode_token(authorization.split(" ")[1])
    
    if not token_data or token_data.get("step") != "fully_authenticated":
        raise HTTPException(status_code=403, detail="Biometric Verification Required for AI Access")
    
    user = db.query(User).filter(User.render_url == token_data["sub"]).first()
    if not user.membership_active:
        raise HTTPException(status_code=402, detail="Active Membership Required. Please scan QR to upgrade.")

    if not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="AI Core Offline. Awaiting API Key.")

    try:
        formatted_history = [{"role": m["role"], "parts": [m["content"]]} for m in payload.history]
        chat_session = ai_model.start_chat(history=formatted_history)
        response = chat_session.send_message(payload.message)
        return {"reply": response.text}
    except Exception as e:
        logger.error(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
