from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from openai import OpenAI

app = FastAPI()

# CORS (frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok", "message": "GPT AI Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# 🔥 REAL AI ENDPOINT
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": req.message}
            ]
        )

        reply = response.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
