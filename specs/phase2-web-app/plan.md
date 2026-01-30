# Implementation Plan: Phase II - Full-Stack Todo Web Application

**Branch**: `master` | **Date**: 2026-01-29 | **Spec**: `specs/phase2-web-app/spec.md`
**Input**: Feature specification from `specs/phase2-web-app/spec.md`
**Status**: Implemented

## Summary

Transform the Phase I Python console todo app into a full-stack web application. The system uses a monorepo with a Next.js 15 frontend (App Router, TypeScript, Tailwind CSS), a FastAPI backend (SQLModel ORM), Neon PostgreSQL for persistence, and Better Auth with JWT (EdDSA via JWKS) for authentication. Users register and sign in on the frontend, receive JWT tokens, and interact with a REST API on the backend for task CRUD operations.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.115, SQLModel 0.0.22, PyJWT 2.10.1, Next.js 16.1.5, Better Auth 1.4.17, React 19.2.3, Tailwind CSS 4.x
**Storage**: Neon PostgreSQL (serverless, connection pooler, `sslmode=require`)
**Testing**: curl-based E2E tests (dev.test-e2e skill), FastAPI /docs for manual testing
**Target Platform**: Linux server (development), web browser (client)
**Project Type**: Web application (frontend + backend monorepo)
**Performance Goals**: Single-user development; no high-concurrency requirements
**Constraints**: Neon drops idle connections (mitigated with pool_pre_ping), Better Auth uses EdDSA JWT (not HS256), `channel_binding=require` must NOT be in connection URLs
**Scale/Scope**: Single developer, < 1000 tasks per user, local development

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | spec.md written before plan; plan precedes tasks |
| II. Minimal Viable Implementation | PASS | CRUD + auth only; no extras |
| III. Clean Code Standards | PASS | Type hints (Python), TypeScript (frontend), PEP 8, single responsibility |
| IV. Test-First Approach | PARTIAL | E2E test skill exists; unit tests not yet added |
| V. Modular Architecture | PASS | Backend: routes/models/schemas/auth separated; Frontend: lib/types/app separated |
| VI. User Experience First | PASS | Clear UI, error messages, loading states, feedback on actions |

**Gate Result**: PASS (test-first is partial but E2E coverage exists)

## Project Structure

### Documentation (this feature)

```text
specs/phase2-web-app/
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 developer quickstart
├── contracts/           # Phase 1 API contracts
│   └── openapi.yaml     # OpenAPI 3.0 specification
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py          # FastAPI entry, CORS, lifespan, root + health routes
│   ├── models.py        # Task SQLModel table definition
│   ├── db.py            # Engine (pool_pre_ping, pool_recycle), session factory
│   ├── schemas.py       # TaskCreate, TaskUpdate Pydantic schemas
│   ├── auth.py          # JWKS-based JWT verification (PyJWT + PyJWKClient)
│   └── routes/
│       └── tasks.py     # 6 CRUD endpoints under /api/{user_id}/tasks
├── .env                 # DATABASE_URL, BETTER_AUTH_SECRET
└── requirements.txt     # fastapi, uvicorn, sqlmodel, psycopg2-binary, PyJWT, dotenv

frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout (Geist fonts, Tailwind)
│   │   ├── page.tsx             # Dashboard: task list, add/edit/delete/toggle
│   │   ├── sign-in/page.tsx     # Sign-in form
│   │   ├── sign-up/page.tsx     # Sign-up form
│   │   └── api/auth/[...all]/route.ts  # Better Auth catch-all API handler
│   ├── lib/
│   │   ├── auth.ts              # Better Auth server config (pg.Pool + JWT plugin)
│   │   ├── auth-client.ts       # Better Auth React client (jwtClient plugin)
│   │   └── api.ts               # API client: fetchWithAuth + 5 methods
│   ├── components/              # (extensible)
│   └── types/
│       └── task.ts              # Task TypeScript interface
├── .env.local                   # Secrets and API URLs
├── package.json
├── next.config.ts
└── tailwind.config.ts

.claude/
├── agents/
│   ├── backend.md               # FastAPI specialist agent
│   ├── frontend.md              # Next.js specialist agent
│   ├── fullstack.md             # Cross-cutting coordinator agent
│   └── database.md              # Neon PostgreSQL specialist agent
└── commands/
    ├── dev.start.md             # Start both servers
    ├── dev.stop.md              # Stop both servers
    ├── dev.test-e2e.md          # Full E2E test suite
    ├── dev.db-migrate.md        # Run database migrations
    ├── dev.add-route.md         # Add new API endpoint (backend + frontend)
    └── dev.add-page.md          # Add new frontend page
```

**Structure Decision**: Web application (Option 2) — frontend/ and backend/ as separate projects in a monorepo, with shared Neon PostgreSQL database. Agents and skills in `.claude/` directory for Claude Code automation.

## Phase 0: Research

### R-001: Better Auth JWT Algorithm

- **Decision**: Better Auth uses EdDSA asymmetric signing (not HS256)
- **Rationale**: Better Auth auto-generates EdDSA key pairs stored in `jwks` table; tokens are verified via a JWKS endpoint, not shared secret
- **Alternatives considered**: HS256 with shared secret (failed - Better Auth doesn't support it), RS256 (not the default)
- **Impact**: Backend must use `PyJWKClient` to fetch public keys from `http://localhost:3000/api/auth/jwks`

### R-002: Better Auth Database Adapter

- **Decision**: Pass `pg.Pool` instance directly as `database` option
- **Rationale**: Better Auth's internal Kysely adapter requires a Pool instance, not a `{ type, url }` config object
- **Alternatives considered**: `{ type: "postgres", url: "..." }` config (failed with "Failed to initialize database adapter")

### R-003: Neon PostgreSQL Connection Management

- **Decision**: Use `pool_pre_ping=True` and `pool_recycle=300` on SQLAlchemy engine
- **Rationale**: Neon's serverless architecture drops idle connections; these settings ensure automatic reconnection
- **Alternatives considered**: Manual reconnect logic (over-engineered), no mitigation (causes "SSL connection has been closed unexpectedly" errors)
- **Additional**: Remove `channel_binding=require` from all connection strings to avoid pg library compatibility issues

### R-004: Token Extraction Pattern

- **Decision**: `authClient.token()` returns `{ data: { token: string } }` shape
- **Rationale**: Better Auth's jwtClient plugin wraps the token in a data envelope
- **Pattern**: `(res as { data?: { token?: string } })?.data?.token`
- **Alternatives considered**: `authClient.getToken()` (doesn't exist), direct property access (type errors)

### R-005: Better Auth Migration Strategy

- **Decision**: Use `npx @better-auth/cli migrate --yes` for auth tables, SQLModel auto-creates app tables on startup
- **Rationale**: Better Auth manages its own schema (user, session, account, verification, jwks); SQLModel manages the tasks table independently
- **Dependencies**: Node.js and npm in frontend directory, DATABASE_URL environment variable

See also: `specs/phase2-web-app/research.md` for full research notes.

## Phase 1: Design

### 1.1 Data Model

See `specs/phase2-web-app/data-model.md` for full entity definitions.

**Entities**:
- **User** (Better Auth managed): UUID id, name, email, emailVerified, image, timestamps
- **Session** (Better Auth managed): session token, expiry, user association
- **Account** (Better Auth managed): provider credentials linked to user
- **JWKS** (Better Auth managed): EdDSA key pairs for JWT signing
- **Task** (Application managed): auto-increment id, user_id FK, title, description, completed, timestamps

**Key Relationships**:
- User 1:N Task (via `user_id` string FK)
- User 1:N Session (managed by Better Auth)
- User 1:N Account (managed by Better Auth)

### 1.2 API Contracts

See `specs/phase2-web-app/contracts/openapi.yaml` for full OpenAPI 3.0 specification.

**Endpoints**:

| Method | Path | Auth | Description | Status Codes |
|--------|------|------|-------------|-------------|
| GET | `/api/{user_id}/tasks` | JWT | List all tasks for user | 200, 401, 403 |
| POST | `/api/{user_id}/tasks` | JWT | Create a new task | 201, 401, 403, 422 |
| GET | `/api/{user_id}/tasks/{task_id}` | JWT | Get single task | 200, 401, 403, 404 |
| PUT | `/api/{user_id}/tasks/{task_id}` | JWT | Update task fields | 200, 401, 403, 404, 422 |
| DELETE | `/api/{user_id}/tasks/{task_id}` | JWT | Delete a task | 204, 401, 403, 404 |
| PATCH | `/api/{user_id}/tasks/{task_id}/complete` | JWT | Toggle completion | 200, 401, 403, 404 |
| GET | `/` | None | API info | 200 |
| GET | `/health` | None | Health check | 200 |

### 1.3 Authentication Architecture

```
┌─────────────┐     sign-up/in      ┌──────────────────┐
│   Browser    │ ──────────────────> │  Next.js (3000)  │
│              │ <── session cookie  │  Better Auth     │
│              │                     │  + JWT plugin    │
│              │     token()         │  + pg.Pool → DB  │
│              │ ──────────────────> │                  │
│              │ <── JWT (EdDSA)     │  JWKS endpoint   │
│              │                     └──────────────────┘
│              │                            │
│              │     API + Bearer JWT       │ JWKS public keys
│              │ ──────────────> ┌──────────┴──────────┐
│              │ <── JSON data   │  FastAPI (8000)     │
└─────────────┘                  │  PyJWT + PyJWKClient│
                                 │  SQLModel → DB      │
                                 └─────────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ Neon PostgreSQL  │
                                 │ (cloud, pooler)  │
                                 └─────────────────┘
```

### 1.4 Agents & Skills Architecture

**Agents** (`.claude/agents/`): Specialist context files that inform Claude Code about domain-specific patterns.

| Agent | Scope | Key Responsibility |
|-------|-------|--------------------|
| `backend.md` | FastAPI, SQLModel, auth | API routes, JWT verification, DB models |
| `frontend.md` | Next.js, Better Auth, React | Pages, auth flow, API client, UI |
| `fullstack.md` | Cross-cutting | Coordination, E2E, architecture |
| `database.md` | Neon PostgreSQL | Schema, migrations, connection management |

**Skills** (`.claude/commands/dev.*.md`): Executable development workflows.

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `dev.start` | `/dev.start` | Start backend + frontend servers |
| `dev.stop` | `/dev.stop` | Kill all dev server processes |
| `dev.test-e2e` | `/dev.test-e2e` | Run full auth + CRUD E2E test suite |
| `dev.db-migrate` | `/dev.db-migrate` | Run Better Auth + backend migrations |
| `dev.add-route` | `/dev.add-route` | Scaffold new API endpoint (both sides) |
| `dev.add-page` | `/dev.add-page` | Scaffold new frontend page |

### 1.5 Frontend Pages

| Route | Page | Auth | Purpose |
|-------|------|------|---------|
| `/` | `page.tsx` | Required | Main dashboard — task list, add/edit/delete/toggle |
| `/sign-up` | `sign-up/page.tsx` | Public | Registration form |
| `/sign-in` | `sign-in/page.tsx` | Public | Login form |
| `/api/auth/[...all]` | `route.ts` | N/A | Better Auth API handler (catch-all) |

## Implementation Order

### Layer 1: Foundation (Backend)
1. Project scaffold: `backend/` directory, `requirements.txt`, `.env`
2. Database connection: `db.py` with Neon-compatible engine settings
3. Task model: `models.py` with SQLModel table definition
4. Schemas: `schemas.py` with Pydantic request/response models

### Layer 2: API (Backend)
5. Auth middleware: `auth.py` with JWKS-based JWT verification
6. Task routes: `routes/tasks.py` with 6 CRUD endpoints
7. FastAPI app: `main.py` with CORS, lifespan, router inclusion

### Layer 3: Foundation (Frontend)
8. Next.js project: `create-next-app` with TypeScript + Tailwind
9. Better Auth server: `auth.ts` with pg.Pool + JWT plugin
10. Better Auth client: `auth-client.ts` with jwtClient plugin
11. Auth API handler: `api/auth/[...all]/route.ts`

### Layer 4: UI (Frontend)
12. Auth pages: `sign-up/page.tsx`, `sign-in/page.tsx`
13. API client: `api.ts` with fetchWithAuth + 5 endpoint methods
14. Dashboard: `page.tsx` with task list, add/edit/delete/toggle forms
15. Types: `types/task.ts`

### Layer 5: DevOps (Agents & Skills)
16. Agents: `backend.md`, `frontend.md`, `fullstack.md`, `database.md`
17. Skills: `dev.start.md`, `dev.stop.md`, `dev.test-e2e.md`, `dev.db-migrate.md`, `dev.add-route.md`, `dev.add-page.md`

### Layer 6: Verification
18. Database migrations: Better Auth CLI + SQLModel auto-create
19. E2E testing: sign-up → sign-in → JWT → CRUD → auth rejection
20. Spec + plan documentation

## Complexity Tracking

No constitution violations requiring justification. The two-project monorepo (frontend + backend) is the natural structure for a web application with separate language stacks.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Neon connection drops | API errors | `pool_pre_ping=True`, `pool_recycle=300` |
| Better Auth API changes | Auth breakage | Pin `better-auth@^1.4.17` in package.json |
| JWKS endpoint unreachable | All API calls fail | Backend returns 401; frontend redirects to sign-in |

## Follow-ups

1. Add unit tests for backend routes (pytest + httpx test client)
2. Add frontend component tests (React Testing Library)
3. Deploy to production (Docker + cloud hosting)
