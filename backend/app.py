# backend/main.py (or merge into your existing app)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Protected Ethical Anis AI")

# Allow the frontend origin(s). For simplicity allow all origins during initial setup.
# For production, replace "*" with your Vercel URL: "https://your-frontend.vercel.app"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- change to your Vercel URL when ready
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "message": "backend healthy"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Protected Ethical Anis AI backend running"}
