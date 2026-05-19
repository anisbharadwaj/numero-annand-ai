from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router

app = FastAPI()

# CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTH ROUTES
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "AI backend running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# SIMPLE CHAT ENDPOINT (IMPORTANT)
@app.post("/chat")
def chat(data: dict):
    msg = data.get("message", "")
    return {"reply": "AI Response: " + msg}
