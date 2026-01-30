# Tasks: Phase II - Full-Stack Todo Web Application

**Input**: Design documents from `/specs/phase2-web-app/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not explicitly requested. E2E testing via `dev.test-e2e` skill covers acceptance criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app monorepo**: `backend/app/`, `frontend/src/`
- **Agents**: `.claude/agents/`
- **Skills**: `.claude/commands/`
- **Specs**: `specs/phase2-web-app/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, dependency management

- [x] T001 Create backend project directory structure: `backend/`, `backend/app/`, `backend/app/routes/`
- [x] T002 [P] Create `backend/requirements.txt` with fastapi[standard]==0.115.0, uvicorn[standard]==0.30.0, sqlmodel==0.0.22, psycopg2-binary==2.9.9, PyJWT[crypto]==2.10.1, python-dotenv==1.0.1
- [x] T003 [P] Create `backend/.env` with DATABASE_URL and BETTER_AUTH_SECRET (never commit; add to .gitignore)
- [x] T004 [P] Create Python virtual environment and install dependencies: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- [x] T005 Initialize frontend with Next.js 16: `npx create-next-app@latest frontend` (TypeScript, Tailwind CSS, App Router, Turbopack)
- [x] T006 Install frontend auth dependency: `cd frontend && npm install better-auth pg`
- [x] T007 [P] Create `frontend/.env.local` with BETTER_AUTH_SECRET, BETTER_AUTH_URL, DATABASE_URL, NEXT_PUBLIC_API_URL, NEXT_PUBLIC_BETTER_AUTH_URL
- [x] T008 [P] Create/update `.gitignore` to exclude `.env`, `.env.local`, `__pycache__`, `.venv`, `node_modules`, `.next`

**Checkpoint**: Both projects initialized with dependencies installed and env files configured.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T009 Create database engine with Neon-compatible settings in `backend/app/db.py`: SQLModel engine with `pool_pre_ping=True`, `pool_recycle=300`, `get_session` dependency, `create_db_and_tables` function
- [x] T010 [P] Create Task SQLModel table in `backend/app/models.py`: id (int PK auto-increment), user_id (str indexed), title (str), description (str default ""), completed (bool default False), created_at (datetime UTC), updated_at (datetime UTC)
- [x] T011 [P] Create Pydantic request schemas in `backend/app/schemas.py`: TaskCreate (title required, description optional), TaskUpdate (title/description/completed all optional)
- [x] T012 [P] Create JWKS-based JWT verification in `backend/app/auth.py`: PyJWKClient fetching from `http://localhost:3000/api/auth/jwks`, `verify_token` dependency using Security(HTTPBearer), `get_user_id` helper extracting `sub` claim, accept algorithms ["EdDSA", "ES256", "RS256", "PS256"]
- [x] T013 Create FastAPI app entry point in `backend/app/main.py`: lifespan creating tables, CORSMiddleware allowing `http://localhost:3000`, root `/` route returning API info, `/health` route

### Frontend Foundation

- [x] T014 Create Better Auth server config in `frontend/src/lib/auth.ts`: import pg.Pool, create pool with DATABASE_URL, export betterAuth with database=pool, plugins=[jwt()], emailAndPassword enabled
- [x] T015 [P] Create Better Auth React client in `frontend/src/lib/auth-client.ts`: createAuthClient with baseURL and jwtClient plugin, export signIn, signUp, signOut, useSession
- [x] T016 [P] Create Task TypeScript interface in `frontend/src/types/task.ts`: id (number), user_id (string), title (string), description (string), completed (boolean), created_at (string), updated_at (string)
- [x] T017 Create Better Auth catch-all API handler in `frontend/src/app/api/auth/[...all]/route.ts`: import auth from lib/auth, export GET and POST handlers via `auth.handler`
- [x] T018 Create API client with Bearer auth in `frontend/src/lib/api.ts`: fetchWithAuth helper (adds Authorization header), api object with listTasks, createTask, updateTask, deleteTask, toggleComplete methods

### Database Migration

- [x] T019 Run Better Auth database migration: `cd frontend && DATABASE_URL="..." npx @better-auth/cli migrate --yes` — creates user, session, account, verification, jwks tables
- [x] T020 Start backend briefly to auto-create tasks table: `cd backend && .venv/bin/uvicorn app.main:app --port 8000` — SQLModel.metadata.create_all runs in lifespan

**Checkpoint**: Foundation ready — backend API skeleton running on port 8000, frontend auth configured on port 3000, database tables created. User story implementation can now begin.

---

## Phase 3: User Story 1 - User Registration (Priority: P1) MVP

**Goal**: New users can create an account with name, email, and password and be redirected to the dashboard.

**Independent Test**: Navigate to `/sign-up`, fill in name/email/password, verify account created and redirected to `/`.

### Implementation for User Story 1

- [x] T021 [US1] Create sign-up page in `frontend/src/app/sign-up/page.tsx`: "use client" component with name/email/password form, call `signUp.email()` from auth-client, handle success (redirect to `/`) and error (display message), Tailwind styled (gray-50 bg, white card, blue-600 buttons)
- [x] T022 [US1] Add navigation link from sign-up to sign-in: include "Already have an account? Sign In" link at bottom of `frontend/src/app/sign-up/page.tsx`

**Checkpoint**: User Story 1 complete — users can register via `/sign-up` and are redirected to dashboard.

---

## Phase 4: User Story 2 - User Sign-In / Sign-Out (Priority: P1)

**Goal**: Existing users can sign in with email/password to access tasks. They can sign out to end the session. Unauthenticated users are redirected to sign-in.

**Independent Test**: Sign in with valid credentials → verify dashboard access. Click "Sign Out" → verify redirect to `/sign-in`. Visit `/` while unauthenticated → verify redirect.

### Implementation for User Story 2

- [x] T023 [US2] Create sign-in page in `frontend/src/app/sign-in/page.tsx`: "use client" component with email/password form, call `signIn.email()` from auth-client, handle success (redirect to `/`) and error (display message), Tailwind styled
- [x] T024 [US2] Add navigation link from sign-in to sign-up: include "Don't have an account? Sign Up" link at bottom of `frontend/src/app/sign-in/page.tsx`
- [x] T025 [US2] Create main dashboard page shell in `frontend/src/app/page.tsx`: "use client" component, useSession hook, useEffect to redirect unauthenticated users to `/sign-in`, loading state, sign-out button calling `signOut()` then redirect, display user email in header

**Checkpoint**: User Story 2 complete — users can sign in, see dashboard, sign out. Unauthenticated users are redirected.

---

## Phase 5: User Story 3 - Create a Task (Priority: P1)

**Goal**: Authenticated users can create a new task by entering a title. The task appears in the list immediately.

**Independent Test**: Sign in, enter task title, click "Add", verify task appears in list.

### Implementation for User Story 3

- [x] T026 [US3] Create backend POST route in `backend/app/routes/tasks.py`: `POST /{user_id}/tasks` with TaskCreate body, JWT auth dependency, owner validation, create Task in DB, return 201 with task JSON
- [x] T027 [US3] Include tasks router in FastAPI app: add `app.include_router(tasks_router)` in `backend/app/main.py`
- [x] T028 [US3] Add JWT token extraction helper in `frontend/src/app/page.tsx`: `getToken()` async function calling `authClient.token()`, extract token from `{ data: { token: string } }` response shape
- [x] T029 [US3] Add task creation form to dashboard in `frontend/src/app/page.tsx`: title input, optional description input, "Add Task" submit button, `handleAdd` calling `api.createTask()` with JWT, clear form and reload tasks on success

**Checkpoint**: User Story 3 complete — authenticated users can create tasks via the dashboard form.

---

## Phase 6: User Story 4 - View Task List (Priority: P1)

**Goal**: Authenticated users see all their tasks on the dashboard, ordered by creation time.

**Independent Test**: Create several tasks, reload dashboard, verify all tasks displayed. Different user sees only their own tasks.

### Implementation for User Story 4

- [x] T030 [US4] Create backend GET route in `backend/app/routes/tasks.py`: `GET /{user_id}/tasks` returning list of tasks filtered by user_id, with JWT auth and owner validation
- [x] T031 [US4] Add task list loading to dashboard in `frontend/src/app/page.tsx`: `loadTasks()` callback fetching tasks via `api.listTasks()` with JWT, `useEffect` triggering on session change, render tasks with title, description, completed status
- [x] T032 [US4] Add empty state message in `frontend/src/app/page.tsx`: show "No tasks yet. Add one above!" when tasks array is empty

**Checkpoint**: User Story 4 complete — authenticated users see their task list on dashboard load. Empty state handled.

---

## Phase 7: User Story 5 - Toggle Task Completion (Priority: P2)

**Goal**: Users can mark tasks as complete/incomplete by clicking a checkbox.

**Independent Test**: Click checkbox on incomplete task → verify strikethrough and checkmark. Click again → verify reverted.

### Implementation for User Story 5

- [x] T033 [US5] Create backend PATCH route in `backend/app/routes/tasks.py`: `PATCH /{user_id}/tasks/{task_id}/complete` toggling `task.completed`, updating `updated_at`, JWT auth and owner validation
- [x] T034 [US5] Add toggle UI to dashboard in `frontend/src/app/page.tsx`: checkbox input bound to `task.completed`, `handleToggle()` calling `api.toggleComplete()`, reload tasks after toggle, strikethrough + gray text for completed tasks

**Checkpoint**: User Story 5 complete — users can toggle task completion via checkbox.

---

## Phase 8: User Story 6 - Delete a Task (Priority: P2)

**Goal**: Users can delete tasks they no longer need.

**Independent Test**: Click "Delete" on a task → verify it disappears from the list.

### Implementation for User Story 6

- [x] T035 [US6] Create backend DELETE route in `backend/app/routes/tasks.py`: `DELETE /{user_id}/tasks/{task_id}` returning 204, JWT auth, owner validation, 404 if not found
- [x] T036 [US6] Add delete button to task items in `frontend/src/app/page.tsx`: red "Delete" button, `handleDelete()` calling `api.deleteTask()`, reload tasks after deletion

**Checkpoint**: User Story 6 complete — users can delete tasks from their list.

---

## Phase 9: User Story 7 - Update a Task (Priority: P3)

**Goal**: Users can edit the title or description of an existing task.

**Independent Test**: Click "Edit" on a task → modify title → click "Save" → verify updated title persists.

### Implementation for User Story 7

- [x] T037 [US7] Create backend PUT route in `backend/app/routes/tasks.py`: `PUT /{user_id}/tasks/{task_id}` accepting TaskUpdate body, partial update with `model_dump(exclude_unset=True)`, update `updated_at`, JWT auth and owner validation
- [x] T038 [US7] Create backend GET single task route in `backend/app/routes/tasks.py`: `GET /{user_id}/tasks/{task_id}` returning single task, JWT auth, owner validation, 404 if not found
- [x] T039 [US7] Add inline edit UI to dashboard in `frontend/src/app/page.tsx`: "Edit" button toggling edit mode per task (`editingId` state), edit form with title/description inputs, "Save" button calling `api.updateTask()`, "Cancel" button to exit edit mode, reload tasks after save

**Checkpoint**: User Story 7 complete — users can inline-edit task title and description.

---

## Phase 10: DevOps - Agents & Skills

**Purpose**: Claude Code automation for development workflow

### Agents

- [x] T040 [P] Create backend agent in `.claude/agents/backend.md`: FastAPI specialist with tech stack, project structure, key patterns (JWKS auth, owner validation, Neon pooling), rules, commands
- [x] T041 [P] Create frontend agent in `.claude/agents/frontend.md`: Next.js specialist with tech stack, project structure, auth flow (Better Auth → JWT → Bearer), key patterns ("use client", useSession, getToken), rules, commands
- [x] T042 [P] Create fullstack agent in `.claude/agents/fullstack.md`: Cross-cutting coordinator with architecture overview, auth flow, database notes, API contract table, environment variables, rules, startup commands
- [x] T043 [P] Create database agent in `.claude/agents/database.md`: Neon PostgreSQL specialist with table schemas (Better Auth managed + application managed), key constraints (pool_pre_ping, no channel_binding), migration commands, common queries

### Skills

- [x] T044 [P] Create dev.start skill in `.claude/commands/dev.start.md`: kill stale processes on ports 3000/3001/8000, remove Next.js lock file, start backend (uvicorn background), start frontend (npm run dev background), verify both servers with curl
- [x] T045 [P] Create dev.stop skill in `.claude/commands/dev.stop.md`: kill processes on ports 3000/3001/8000, remove lock file, verify ports free
- [x] T046 [P] Create dev.test-e2e skill in `.claude/commands/dev.test-e2e.md`: verify servers running, test sign-up (unique email), test sign-in + JWT fetch, test create (201), list (200), toggle (200), update (200), delete (204), auth rejection (403), report results table
- [x] T047 [P] Create dev.db-migrate skill in `.claude/commands/dev.db-migrate.md`: Better Auth migration (npx CLI), backend auto-create on startup, verification query listing tables
- [x] T048 [P] Create dev.add-route skill in `.claude/commands/dev.add-route.md`: parse route description, add backend route handler with JWT auth, update frontend api.ts client, update UI if needed, verify with curl
- [x] T049 [P] Create dev.add-page skill in `.claude/commands/dev.add-page.md`: determine page details from arguments, create page file in app router, create components if needed, add navigation, add API client methods if needed, verify rendering

**Checkpoint**: All agents and skills created — Claude Code can automate development workflows.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T050 [P] Create spec.md in `specs/phase2-web-app/spec.md`: technical specification covering all user stories, functional requirements, entities, architecture, API contract, auth flow
- [x] T051 [P] Create plan.md in `specs/phase2-web-app/plan.md`: implementation plan with technical context, constitution check, project structure, research findings, design, implementation order
- [x] T052 Run E2E test suite via `/dev.test-e2e`: verify all acceptance criteria pass (sign-up, sign-in, JWT, create 201, list 200, toggle 200, update 200, delete 204, auth rejection 403)
- [ ] T053 Validate quickstart.md by following setup steps on clean environment in `specs/phase2-web-app/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - US1 (Registration) and US2 (Sign-In/Out) can run in parallel
  - US3 (Create Task) depends on US2 (needs auth to test)
  - US4 (View List) depends on US3 (needs tasks to view)
  - US5 (Toggle) depends on US4 (needs visible tasks)
  - US6 (Delete) depends on US4 (needs visible tasks), can parallel with US5
  - US7 (Update) depends on US4 (needs visible tasks), can parallel with US5/US6
- **DevOps (Phase 10)**: Independent — can run in parallel with any phase after Setup
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS ALL)
    ↓
  ┌──────────────────┐
  │ US1 Registration  │──┐
  │ US2 Sign-In/Out   │──┤
  └──────────────────┘  │
    ↓                    │
  US3 Create Task ←──────┘
    ↓
  US4 View Task List
    ↓
  ┌─────────────────────────────┐
  │ US5 Toggle (parallel)       │
  │ US6 Delete (parallel)       │
  │ US7 Update (parallel)       │
  └─────────────────────────────┘
    ↓
Phase 10: DevOps (parallel with any)
Phase 11: Polish (after all stories)
```

### Within Each User Story

- Backend route before frontend integration
- Frontend token helper before API calls
- Core implementation before UI refinements

### Parallel Opportunities

- T002, T003, T004 (backend setup files) — all parallel
- T007, T008 (env files + gitignore) — parallel
- T010, T011, T012 (model, schemas, auth) — all parallel within Phase 2
- T014, T015, T016 (frontend auth, client, types) — parallel
- T040-T043 (all agents) — all parallel
- T044-T049 (all skills) — all parallel
- US5, US6, US7 — all parallel after US4

---

## Parallel Example: Phase 2 Foundation

```bash
# Backend foundation (all parallel):
Task: "Create Task SQLModel table in backend/app/models.py"
Task: "Create Pydantic schemas in backend/app/schemas.py"
Task: "Create JWKS JWT verification in backend/app/auth.py"

# Frontend foundation (all parallel):
Task: "Create Better Auth React client in frontend/src/lib/auth-client.ts"
Task: "Create Task TypeScript interface in frontend/src/types/task.ts"
```

## Parallel Example: Phase 10 DevOps

```bash
# All agents (parallel):
Task: "Create backend agent in .claude/agents/backend.md"
Task: "Create frontend agent in .claude/agents/frontend.md"
Task: "Create fullstack agent in .claude/agents/fullstack.md"
Task: "Create database agent in .claude/agents/database.md"

# All skills (parallel):
Task: "Create dev.start skill in .claude/commands/dev.start.md"
Task: "Create dev.stop skill in .claude/commands/dev.stop.md"
Task: "Create dev.test-e2e skill in .claude/commands/dev.test-e2e.md"
Task: "Create dev.db-migrate skill in .claude/commands/dev.db-migrate.md"
Task: "Create dev.add-route skill in .claude/commands/dev.add-route.md"
Task: "Create dev.add-page skill in .claude/commands/dev.add-page.md"
```

---

## Implementation Strategy

### MVP First (User Stories 1-4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Registration)
4. Complete Phase 4: User Story 2 (Sign-In/Out)
5. Complete Phase 5: User Story 3 (Create Task)
6. Complete Phase 6: User Story 4 (View List)
7. **STOP and VALIDATE**: Run E2E tests — users can register, sign in, create, and view tasks

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US2 → Auth flow working (MVP auth)
3. Add US3 + US4 → Task creation + viewing (MVP tasks)
4. Add US5 → Toggle completion
5. Add US6 → Delete tasks
6. Add US7 → Edit tasks
7. Add DevOps → Agents + skills for automation
8. Polish → Spec, plan, E2E validation

### Suggested MVP Scope

**Phases 1-6 (T001-T032)**: 32 tasks delivering registration, sign-in/out, task creation, and task listing. This is the minimum viable product that delivers core value.

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 53 |
| Phase 1 (Setup) | 8 tasks |
| Phase 2 (Foundational) | 12 tasks |
| US1 (Registration) | 2 tasks |
| US2 (Sign-In/Out) | 3 tasks |
| US3 (Create Task) | 4 tasks |
| US4 (View List) | 3 tasks |
| US5 (Toggle) | 2 tasks |
| US6 (Delete) | 2 tasks |
| US7 (Update) | 3 tasks |
| DevOps (Agents+Skills) | 10 tasks |
| Polish | 4 tasks |
| Parallel opportunities | 28 tasks marked [P] |
| MVP scope | Phases 1-6 (32 tasks) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All env files (.env, .env.local) must never be committed
