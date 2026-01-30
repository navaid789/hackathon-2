# Quickstart: AI Chatbot Feature

**Feature**: `001-ai-chatbot` | **Date**: 2026-01-30

## Prerequisites

- Phase II fully working (backend on :8000, frontend on :3000)
- Python 3.12+ with venv at `venv/`
- Node.js 20+
- OpenAI API key (required) and/or Groq API key (optional)

## Setup

### 1. Add API keys to backend environment

Add to `backend/.env`:
```
OPENAI_API_KEY=sk-proj-your-key-here
GROQ_API_KEY=gsk_your-key-here
AI_PROVIDER=openai
```

### 2. Install new backend dependencies

```bash
cd backend
source ../venv/bin/activate
pip install openai groq
```

### 3. Restart servers

```bash
# Kill existing servers
fuser -k 3000/tcp 8000/tcp

# Start backend (creates chat_messages table on startup)
cd backend && ../venv/bin/python -m uvicorn app.main:app --reload --port 8000 &

# Start frontend
cd frontend && npm run dev &
```

### 4. Verify

1. Open http://localhost:3000 and sign in
2. On the dashboard, you should see a chat panel on the right side
3. Type "Show my tasks" and verify the chatbot responds
4. Type "Add a task to buy groceries" and verify the task appears in the list

## New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/{user_id}/chat` | Send a chat message |
| GET | `/api/{user_id}/chat/history?limit=50` | Get chat history |
| DELETE | `/api/{user_id}/chat/history` | Clear chat history |

## New Files

### Backend
- `app/ai_provider.py` — AI provider abstraction (OpenAI + Groq)
- `app/chat_tools.py` — Function-calling tool definitions
- `app/routes/chat.py` — Chat API endpoints

### Frontend
- `src/components/ChatPanel.tsx` — Chat UI component
- `src/types/chat.ts` — TypeScript types for chat

### Modified Files
- `app/models.py` — Added ChatMessage model
- `app/schemas.py` — Added ChatRequest, ChatResponse
- `app/main.py` — Registered chat router
- `frontend/src/lib/api.ts` — Added sendMessage, getChatHistory, clearChatHistory
- `frontend/src/app/dashboard/page.tsx` — Integrated ChatPanel

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes* | — | OpenAI API key |
| `GROQ_API_KEY` | No | — | Groq API key (alternative provider) |
| `AI_PROVIDER` | No | `openai` | Which provider to use: "openai" or "groq" |

*At least one of OPENAI_API_KEY or GROQ_API_KEY must be set.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No AI provider configured" | Set OPENAI_API_KEY or GROQ_API_KEY in backend/.env |
| Chat responses are slow | Switch to Groq (set AI_PROVIDER=groq) for faster inference |
| "Invalid token" errors | Ensure frontend is running on :3000 (JWKS endpoint) |
| Chat panel not visible | Hard refresh the dashboard page (Ctrl+Shift+R) |
