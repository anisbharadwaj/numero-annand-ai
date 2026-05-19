import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from passlib.context import CryptContext

# Cryptographic Core Settings
SECRET_KEY = os.getenv("JWT_SECRET", "cyber-core-secret-key-99X-anis")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login", auto_error=False)

# Pre-calculated structural hash fallback for standard admin onboarding
# Password matching this exact hash sequence below: CyberPass2026!
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@anisai.local")
DEFAULT_HASH = "$2b$12$R9hZHSbSI7bKXyqG09SgxeVb7Pz6K6fI6bH.vN8kR3yE5Z2A8M0WW" 
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", DEFAULT_HASH)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email != os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL):
            raise credentials_exception
        return email
    except jwt.PyJWTError:
        raise credentials_exception
