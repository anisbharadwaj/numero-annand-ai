from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users = {}

# LOGGING
logging.basicConfig(filename="auth.log", level=logging.INFO)

class User(BaseModel):
    username: str
    password: str

# REGISTER
@router.post("/register")
def register(user: User):
    if user.username in users:
        logging.warning("Register failed: user exists")
        raise HTTPException(400, "User already exists")

    hashed = pwd_context.hash(user.password)
    users[user.username] = hashed

    logging.info(f"User registered: {user.username}")
    return {"message": "registered successfully"}

# LOGIN
@router.post("/login")
def login(user: User):
    if user.username not in users:
        raise HTTPException(400, "User not found")

    if not pwd_context.verify(user.password, users[user.username]):
        raise HTTPException(400, "Invalid password")

    # SIMPLE TOKEN (upgrade later to JWT)
    token = user.username + "_token"

    logging.info(f"Login success: {user.username}")
    return {"token": token}
