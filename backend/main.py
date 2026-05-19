from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta

from database import SessionLocal
from auth import User, hash_password, verify_password

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"

# ---------------- MODELS ----------------
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    token: str

# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# ---------------- REGISTER ----------------
@app.post("/register")
def register(req: RegisterRequest):
    db = SessionLocal()

    user = db.query(User).filter(User.username == req.username).first()

    if user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        username=req.username,
        password=hash_password(req.password)
    )

    db.add(new_user)
    db.commit()
    db.close()

    return {"message": "User registered successfully"}

# ---------------- LOGIN ----------------
@app.post("/login")
def login(req: LoginRequest):
    db = SessionLocal()

    user = db.query(User).filter(User.username == req.username).first()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {
            "sub": user.username,
            "exp": datetime.utcnow() + timedelta(hours=2)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    db.close()
    return {"token": token}

# ---------------- CHAT ----------------
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"reply": f"AI Response: {req.message}"}

@app.get("/")
def root():
    return {"status": "ok", "message": "AI System Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
