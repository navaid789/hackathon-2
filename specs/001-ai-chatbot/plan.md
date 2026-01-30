# Implementation Plan: AI Chatbot with Natural Language Task Management

**Branch**: `001-ai-chatbot` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-chatbot/spec.md`

## Summary

Add an AI-powered chat interface to the TaskFlow dashboard that lets users manage tasks through natural language. The backend will expose a `/api/{user_id}/chat` endpoint that receives messages, calls an AI provider (OpenAI or Groq) with function-calling tools mapped to existing task CRUD operations, executes the resulting actions, and returns a human-friendly response. The frontend will render a chat side panel on the dashboard with message bubbles, typing indicator, and auto-scroll.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.115, OpenAI Python SDK, Groq Python SDK, Next.js 15.5.7, React 18
**Storage**: Neon PostgreSQL (existing) — new `chat_messages` table for history
**Testing**: curl-based E2E tests (existing pattern), manual testing
**Target Platform**: Web (localhost:3000 frontend, localhost:8000 backend)
**Project Type**: Web application (monorepo: backend/ + frontend/)
**Performance Goals**: <5s response time per chat message (AI provider latency dominant)
**Constraints**: API keys stored as env vars only; AI processing server-side only; no client-side AI calls
**Scale/Scope**: Single-user chat sessions, ~50 messages per session context window

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is a placeholder template (not yet filled in). No gates to evaluate. Proceeding with project-level guidelines from CLAUDE.md:

| Principle | Status | Notes |
|-----------|--------|-------|
| Smallest viable diff | PASS | Extends existing backend/frontend; no new services |
| No hardcoded secrets | PASS | API keys via .env; never in code or version control |
| Clarify and plan first | PASS | Spec complete, plan in progress |
| Do not invent APIs | PASS | Chat endpoint follows existing task API patterns |

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # Chat endpoint OpenAPI spec
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py           # Add chat router import
│   ├── models.py          # Add ChatMessage model
│   ├── schemas.py         # Add ChatRequest, ChatResponse schemas
│   ├── ai_provider.py     # NEW: OpenAI/Groq abstraction layer
│   ├── chat_tools.py      # NEW: Function-calling tool definitions
│   └── routes/
│       ├── tasks.py       # Existing (unchanged)
│       └── chat.py        # NEW: Chat endpoint
└── requirements.txt       # Add openai, groq

frontend/
├── src/
│   ├── app/
│   │   └── dashboard/
│   │       └── page.tsx   # Add ChatPanel integration
│   ├── components/
│   │   └── ChatPanel.tsx  # NEW: Chat UI component
│   ├── lib/
│   │   └── api.ts         # Add sendMessage method
│   └── types/
│       └── chat.ts        # NEW: Chat TypeScript types
```

**Structure Decision**: Extends existing monorepo structure. Backend gets 3 new files (`ai_provider.py`, `chat_tools.py`, `routes/chat.py`). Frontend gets 2 new files (`ChatPanel.tsx`, `types/chat.ts`). Existing files modified minimally.

## Architecture

### AI Function-Calling Flow

```
User types message in ChatPanel
  → Frontend POST /api/{user_id}/chat { message, history }
    → Backend receives, verifies JWT (same auth as tasks)
    → Backend fetches user's current tasks from DB
    → Backend builds system prompt with task context
    → Backend calls AI provider with tools:
        - create_task(title, description)
        - list_tasks()
        - complete_task(task_id)
        - delete_task(task_id)
        - update_task(task_id, title, description)
    → AI returns tool_calls or text response
    → If tool_calls: Backend executes against DB, sends results back to AI
    → AI generates human-friendly response
    → Backend saves messages to chat_messages table
    → Backend returns { reply, action_taken, task_data }
  → Frontend displays response, refreshes task list if action taken
```

### AI Provider Abstraction

```
ai_provider.py
  ├── AIProvider (protocol/interface)
  │   └── chat(messages, tools) → response
  ├── OpenAIProvider
  │   └── Uses openai SDK, model: gpt-4o-mini
  └── GroqProvider
      └── Uses groq SDK (OpenAI-compatible), model: llama-3.3-70b-versatile

get_provider() → reads AI_PROVIDER env var → returns appropriate provider
  Default: "openai" if OPENAI_API_KEY set, else "groq"
```

### Tool Definitions

Five tools mapped to existing task CRUD, defined as OpenAI-compatible function schemas:

| Tool | Parameters | Maps To |
|------|-----------|---------|
| `create_task` | title (str), description (str, optional) | POST /tasks |
| `list_tasks` | none | GET /tasks |
| `complete_task` | task_id (int) | PATCH /tasks/{id}/complete |
| `delete_task` | task_id (int) | DELETE /tasks/{id} |
| `update_task` | task_id (int), title (str, optional), description (str, optional) | PUT /tasks/{id} |

## Implementation Order

### Layer 1: Backend AI Foundation (BLOCKING)
1. `ai_provider.py` — Provider abstraction + OpenAI implementation
2. `chat_tools.py` — Tool definitions as JSON schemas
3. Add `openai` and `groq` to `requirements.txt`

### Layer 2: Backend Chat Endpoint
4. `ChatMessage` model in `models.py`
5. `ChatRequest` / `ChatResponse` schemas in `schemas.py`
6. `routes/chat.py` — Chat endpoint with tool execution loop
7. Register chat router in `main.py`

### Layer 3: Frontend Chat UI
8. `types/chat.ts` — ChatMessage, ChatResponse types
9. `api.ts` — Add `sendMessage()` method
10. `ChatPanel.tsx` — Chat side panel component
11. `dashboard/page.tsx` — Integrate ChatPanel

### Layer 4: Enhancements
12. Groq provider implementation in `ai_provider.py`
13. Chat history persistence (load on mount, clear button)

### Layer 5: Verification
14. E2E test: chat create/list/complete/delete via curl
15. Manual testing of conversational flow

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI provider latency >5s | Poor UX, timeouts | Use streaming or show typing indicator; use gpt-4o-mini (fast); Groq as fast fallback |
| AI misinterprets user intent | Wrong task action | Confirm destructive actions; include task list context in prompt; use strict function calling |
| API key exposure | Security breach | Server-side only; env vars; never in frontend code; .env in .gitignore |
| Tool call loop (AI keeps calling tools) | Infinite loop, cost | Max 5 tool calls per request; timeout at 30s |

## Complexity Tracking

No constitution violations. The architecture extends existing patterns without adding new services or abstractions beyond what's needed.

## Environment Variables (new)

### Backend (.env) — add to existing
```
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
AI_PROVIDER=openai  # or "groq"
```
