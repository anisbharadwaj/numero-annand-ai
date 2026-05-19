from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 SIMPLE IN-MEMORY DATABASE (safe for deploy)
users = {}
sessions = {}
chat_memory = {}

# ---------- MODELS ----------
class User(BaseModel):
    username: str
    password: str

class Chat(BaseModel):
    token: str
    message: str


# ---------- AUTH ----------
@app.post("/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(400, "User already exists")

    users[user.username] = user.password
    return {"msg": "registered"}

@app.post("/login")
def login(user: User):
    if users.get(user.username) != user.password:
        raise HTTPException(401, "Invalid credentials")

    token = str(uuid.uuid4())
    sessions[token] = user.username
    return {"token": token}


# ---------- CHAT + MEMORY ----------
@app.post("/chat")
def chat(data: Chat):

    if data.token not in sessions:
        raise HTTPException(401, "Invalid token")

    user = sessions[data.token]

    if user not in chat_memory:
        chat_memory[user] = []

    # store user message
    chat_memory[user].append({"role": "user", "text": data.message})

    # AI response (simple engine for now)
    reply = f"🤖 AI: You said '{data.message}'"

    chat_memory[user].append({"role": "ai", "text": reply})

    return {
        "reply": reply,
        "memory": chat_memory[user][-10:]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
