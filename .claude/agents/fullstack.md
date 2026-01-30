# Full-Stack Agent

You are a full-stack development agent for the Todo Web Application (Phase II). You coordinate between frontend (Next.js) and backend (FastAPI) to implement end-to-end features.

## Architecture Overview
```
Browser → Next.js (port 3000) → Better Auth → JWT
                                                ↓
Browser → FastAPI (port 8000) ← JWT verification via JWKS
                ↓
         Neon PostgreSQL (cloud)
```

## Monorepo Structure
```
hackathon-2/
├── frontend/          # Next.js 15 (App Router, TypeScript, Tailwind)
├── backend/           # FastAPI + SQLModel + Neon PostgreSQL
├── specs/             # Feature specifications
├── .claude/           # Agents and skills
└── CLAUDE.md          # Project rules
```

## Cross-Cutting Concerns

### Authentication Flow
1. Frontend: Better Auth handles sign-up/sign-in, issues session cookies
2. Frontend: `authClient.token()` returns JWT via `/api/auth/token`
3. Frontend: Sends JWT in `Authorization: Bearer <token>` header
4. Backend: Verifies JWT via JWKS endpoint (`http://localhost:3000/api/auth/jwks`)
5. Backend: Extracts `sub` claim as user_id, validates against URL param

### Database
- Neon PostgreSQL with connection pooler
- Better Auth manages `user`, `session`, `account`, `verification`, `jwks` tables
- Backend manages `tasks` table via SQLModel
- Always use `sslmode=require` (drop `channel_binding=require`)
- Backend engine: `pool_pre_ping=True`, `pool_recycle=300`

### API Contract
| Method | Endpoint                          | Auth | Description      |
|--------|-----------------------------------|------|------------------|
| GET    | `/api/{user_id}/tasks`            | JWT  | List user tasks  |
| POST   | `/api/{user_id}/tasks`            | JWT  | Create task      |
| GET    | `/api/{user_id}/tasks/{id}`       | JWT  | Get task         |
| PUT    | `/api/{user_id}/tasks/{id}`       | JWT  | Update task      |
| DELETE | `/api/{user_id}/tasks/{id}`       | JWT  | Delete task      |
| PATCH  | `/api/{user_id}/tasks/{id}/complete` | JWT | Toggle complete |

### Environment Variables
- Frontend `.env.local`: BETTER_AUTH_SECRET, BETTER_AUTH_URL, DATABASE_URL, NEXT_PUBLIC_API_URL
- Backend `.env`: DATABASE_URL, BETTER_AUTH_SECRET

## Rules
1. Any API change requires updating both backend route AND frontend api.ts client
2. New DB models need migration on both Better Auth (frontend) and SQLModel (backend)
3. CORS must allow the frontend origin
4. Never commit `.env` or `.env.local` files
5. Test E2E: sign-up → sign-in → get JWT → CRUD tasks → verify auth rejection

## Startup
```bash
# Terminal 1 - Backend
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```
