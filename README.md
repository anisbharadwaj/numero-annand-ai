# Anis-AI-Shield

Secure futuristic AI cybersecurity dashboard with:
- Render URL + password login
- Human verification
- Health check
- Launch button
- Floating AI widget
- Gemini AI responses
- JWT auth
- bcrypt password hashing

## Folder Structure
- backend/
- frontend/

## Backend Setup
Set these environment variables in Render:
- SECRET_KEY
- GEMINI_API_KEY
- INITIAL_USERS
- VERCEL_URL
- DATABASE_URL
- ACCESS_TOKEN_EXPIRE_HOURS

## Login Format
Username: your Render URL  
Password: your unique password

## Render Start Command
uvicorn app:app --host 0.0.0.0 --port $PORT

## Health Check
/health

## Frontend
Deploy the `frontend/` folder on Vercel.

## Notes
- AI replies come from Gemini
- JWT is stored in sessionStorage
- Login is protected by human verification
