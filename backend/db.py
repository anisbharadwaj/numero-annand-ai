from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URL"))

db = client["ultra_ai_v3"]

users = db["users"]
messages = db["messages"]   # 🔥 chat memory
