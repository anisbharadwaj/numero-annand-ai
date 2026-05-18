from fastapi import FastAPI

app = FastAPI(title="Protected Ethical Anis AI")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Protected Ethical Anis AI backend running"}
