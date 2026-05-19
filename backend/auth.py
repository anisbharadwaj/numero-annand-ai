from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "ultra-secret-key-123"
ALGORITHM = "HS256"

# ✅ SIMPLE FAKE DB (NO bcrypt = NO crash)
USERS = {
    "admin": "admin123"
}

def authenticate_user(username, password):
    if username in USERS and USERS[username] == password:
        return {"username": username}
    return None

def create_token(data: dict, expires_minutes=60):
    payload = data.copy()
    payload.update({
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    })
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
