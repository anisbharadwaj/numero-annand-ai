from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

users = {}

class User(BaseModel):
    username: str
    password: str

# REGISTER
@router.post("/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(400, "User already exists")

    users[user.username] = user.password
    return {"msg": "registered successfully"}

# LOGIN
@router.post("/login")
def login(user: User):
    if user.username not in users:
        raise HTTPException(400, "User not found")

    if users[user.username] != user.password:
        raise HTTPException(400, "Wrong password")

    return {"token": user.username}
