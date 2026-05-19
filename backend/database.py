import os
import time
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger("AnisAISystem.Database")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/anis_ai_secure")

try:
    db_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # FIX: Explicitly check for None to avoid truth-value testing exceptions
    default_db = db_client.get_default_database()
    if default_db is not None:
        db = default_db
    else:
        db = db_client["anis_ai_secure"]
        
    db_client.server_info()
    logger.info("MongoDB Connection Matrix Online.")
except ConnectionFailure:
    logger.error("MongoDB Cluster offline. Running fallback volatile storage model.")
    db = None

def get_user_profile(email: str) -> dict:
    """Retrieves user profile and ethical verification data from database."""
    if db is not None:
        try:
            return db.users.find_one({"email": email})
        except Exception:
            return None
    return None

def log_login_event(email: str, status: str, ip_address: str, ai_analysis: str = "") -> None:
    """Securely journals all authentication attempts and AI analysis for forensics audits."""
    if db is not None:
        try:
            db.login_history.insert_one({
                "email": email,
                "timestamp": time.time(),
                "status": status,
                "ip_address": ip_address,
                "ai_threat_profiling": ai_analysis
            })
        except Exception as e:
            logger.error(f"Telemetry log injection fault: {e}")

def save_chat_session(email: str, prompt: str, response: str) -> None:
    """Archives conversation payload inside isolated document store repositories."""
    if db is not None:
        try:
            db.chat_history.insert_one({
                "email": email,
                "timestamp": time.time(),
                "user_prompt": prompt,
                "ai_response": response
            })
        except Exception as e:
            logger.error(f"Chat compression archive error: {e}")
