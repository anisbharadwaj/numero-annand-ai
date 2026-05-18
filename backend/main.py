# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Protected Ethical Anis AI")

# During initial setup allow all origins; replace "*" with your Vercel URL in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "message": "backend healthy"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Protected Ethical Anis AI backend running"}
