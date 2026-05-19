from sqlalchemy import Column, String
from passlib.context import CryptContext
from database import Base, engine, SessionLocal

# password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# USER TABLE
class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# hash password
def hash_password(password):
    return pwd_context.hash(password)

# verify password
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)
