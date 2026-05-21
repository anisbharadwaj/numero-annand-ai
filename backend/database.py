import os
import json

INITIAL_USERS = json.loads(
    os.getenv(
        "INITIAL_USERS",
        '[{"url":"https://protected-ethical-anis-ai-12.onrender.com","pass":"ANIS2H3"}]'
    )
)

def find_user(render_url: str):
    for user in INITIAL_USERS:
        if user["url"].strip() == render_url.strip():
            return user
    return None
