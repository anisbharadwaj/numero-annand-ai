from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import users, messages
from auth import decode_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MEMORY AI ENGINE
def get_memory(user):
    chat_history = messages.find({"user": user}).sort("_id", -1).limit(10)
    return list(chat_history)

def ai_engine(user, msg):
    history = get_memory(user)

    context = " ".join([h["message"] for h in history])

    return f"🤖 AI (memory-aware): {msg} | Context: {context[-200:]}"

@app.post("/chat")
def chat(req: dict):

    data = decode_token(req["token"])
    if not data:
        raise HTTPException(401, "invalid token")

    user = data["user"]
    msg = req["message"]

    reply = ai_engine(user, msg)

    messages.insert_one({
        "user": user,
        "message": msg,
        "reply": reply
    })

    return {"reply": reply}
