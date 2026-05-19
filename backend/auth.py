from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

users = {}

class User(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: User):
    users[user.username] = user.password
    return {"msg": "registered"}

@router.post("/login")
def login(user: User):
    if user.username not in users:
        raise HTTPException(400, "User not found")

    if users[user.username] != user.password:
        raise HTTPException(400, "Wrong password")

    return {"token": user.username}
