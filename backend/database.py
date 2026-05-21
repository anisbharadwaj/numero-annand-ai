import os
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.auth import get_password_hash

logger = logging.getLogger("Anis-AI-Database")

DATABASE_URL = "sqlite:///./anis_shield.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    render_url = Column(String, unique=True, index=True)
    hashed_password = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if we need to seed users from environment variables
    # Format expected in env: [{"url": "https://user1.onrender.com", "pass": "secure1"}]
    seed_data = os.getenv("INITIAL_USERS", "[]")
    try:
        users_to_add = json.loads(seed_data)
        for u in users_to_add:
            existing = db.query(User).filter(User.render_url == u["url"]).first()
            if not existing:
                new_user = User(render_url=u["url"], hashed_password=get_password_hash(u["pass"]))
                db.add(new_user)
                logger.info(f"Seeded user: {u['url']}")
        db.commit()
    except Exception as e:
        logger.error(f"Database seed failed: {e}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
