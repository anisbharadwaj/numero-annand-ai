from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# allow frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "AI backend running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# 🔥 NEW AI CHAT ENDPOINT
@app.post("/chat")
def chat(data: dict):
    user_msg = data.get("message", "")

    # simple AI logic (we can upgrade to OpenAI later)
    reply = f"🤖 AI Response: I received -> {user_msg}"

    return {"reply": reply}
