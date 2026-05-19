from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="Premium Anis AI")

# CORS (Vercel frontend support)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "ok", "message": "Premium AI Backend Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# 🔥 SIMULATED PREMIUM AI ENGINE (no API crash issues)
def ai_engine(text: str):
    text = text.lower()

    if "hello" in text:
        return "👋 Hello! I’m your Premium AI Assistant."
    if "name" in text:
        return "🤖 I am Anis Premium AI System."
    if "help" in text:
        return "🧠 I can answer questions, explain topics, and assist you."
    
    return f"✨ Premium AI Response: {text}"

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        reply = ai_engine(req.message)
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}
