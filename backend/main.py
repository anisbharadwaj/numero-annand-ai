from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS FIX (IMPORTANT FOR VERCEL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "ok", "message": "AI backend running"}

@app.get("/health")
def health():
    return {"status": "ok", "message": "backend healthy"}
