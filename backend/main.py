# (Keep all of your imports and setup configurations at the top of main.py exactly the same)

limiter = Limiter(key_func=get_remote_address)

# UPDATE: Set title metadata registry inside the FastAPI initialization loop
app = FastAPI(title="ANIS-AI-SHIELD Core", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# (Keep all your CORS configurations, logging, and login routes exactly the same)

@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_assistant(query: ChatQuery, current_user: str = Depends(get_current_user)):
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI Core processing interface completely offline.")
    
    try:
        contents = []
        for turn in query.history:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn.get("text", ""))]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=query.message)]))

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                # UPDATE: Instruct the model signature to identify as ANIS-AI-SHIELD
                system_instruction="You are ANIS-AI-SHIELD, an advanced AI system terminal tuned for secure systems administration and ethical hacking optimization. Provide highly intelligent and contextual responses.",
                temperature=0.3
            )
        )
        save_chat_session(current_user, query.message, response.text)
        return {"response": response.text}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal processing error computing generative data streams.")
