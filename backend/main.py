from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import authenticate_user, create_token, decode_token

app = FastAPI(title="ULTRA AI SYSTEM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MODELS ----------
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    token: str

# ---------- LOGIN ----------
@app.post("/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user": req.username})
    return {"token": token}

# ---------- AUTH CHECK ----------
def verify_user(token: str):
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return data

# ---------- ULTRA AI ENGINE ----------
def ai_engine(text: str):
    text = text.lower()

    if "hello" in text:
        return "👋 Hello! I am Ultra AI System."
    if "who are you" in text:
        return "🤖 I am your secure AI assistant with login protection."
    if "name" in text:
        return "🧠 Ultra AI System (Protected Mode)"

    return f"✨ AI Response: {text}"

# ---------- CHAT ----------
@app.post("/chat")
def chat(req: ChatRequest):
    verify_user(req.token)
    return {"reply": ai_engine(req.message)}

@app.get("/")
def root():
    return {"status": "ok", "system": "ULTRA AI ACTIVE"}

@app.get("/health")
def health():
    return {"status": "healthy"}
