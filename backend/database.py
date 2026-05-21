import os
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext

logger = logging.getLogger("Anis-AI-DB")

DATABASE_URL = "sqlite:///./anis_shield.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    render_url = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Security Data
    biometric_enabled = Column(Boolean, default=False)
    webauthn_credential_id = Column(String, nullable=True)
    
    # Membership Data
    membership_tier = Column(String, default="FREE") # FREE, MONTHLY, YEARLY
    membership_active = Column(Boolean, default=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_data = os.getenv("INITIAL_USERS", "[]")
    try:
        users = json.loads(seed_data)
        for u in users:
            if not db.query(User).filter(User.render_url == u["url"]).first():
                new_user = User(
                    render_url=u["url"], 
                    hashed_password=pwd_context.hash(u["pass"]),
                    membership_tier="FREE",
                    membership_active=False
                )
                db.add(new_user)
        db.commit()
    except Exception as e:
        logger.error(f"DB Seed Error: {e}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
