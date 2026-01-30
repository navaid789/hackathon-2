# Feature Specification: Phase II - Full-Stack Todo Web Application

**Feature Branch**: `phase2-web-app`
**Created**: 2026-01-29
**Status**: Implemented
**Input**: User description: "Transform Phase I console todo app into a full-stack web application with Next.js 15 frontend, FastAPI backend, Better Auth JWT authentication, and Neon PostgreSQL database."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Registration (Priority: P1)

A new user visits the application and creates an account using email and password. After registration, they are redirected to the main dashboard where they can start managing tasks.

**Why this priority**: Without registration, no user can access the system. This is the entry point for all functionality.

**Independent Test**: Can be tested by navigating to `/sign-up`, filling in name, email, and password, and verifying the user is created in the database and redirected to `/`.

**Acceptance Scenarios**:

1. **Given** a user is on the sign-up page, **When** they submit a valid name, email, and password, **Then** an account is created and they are redirected to the dashboard.
2. **Given** a user submits an email that already exists, **When** the form is submitted, **Then** an error message is displayed indicating the email is taken.
3. **Given** a user submits an empty or invalid form, **When** the form is submitted, **Then** validation errors are shown.

---

### User Story 2 - User Sign-In / Sign-Out (Priority: P1)

An existing user signs in with their email and password to access their tasks. They can also sign out to end their session.

**Why this priority**: Authentication is required before any task management. Sign-in and sign-out form the core session lifecycle.

**Independent Test**: Can be tested by signing in with valid credentials and verifying dashboard access, then signing out and verifying redirect to sign-in page.

**Acceptance Scenarios**:

1. **Given** a registered user is on the sign-in page, **When** they enter valid credentials, **Then** they are authenticated and redirected to the dashboard.
2. **Given** a user enters invalid credentials, **When** the form is submitted, **Then** an error message is displayed.
3. **Given** an authenticated user clicks "Sign Out", **When** the action completes, **Then** the session is destroyed and the user is redirected to `/sign-in`.
4. **Given** an unauthenticated user visits `/`, **When** the page loads, **Then** they are redirected to `/sign-in`.

---

### User Story 3 - Create a Task (Priority: P1)

An authenticated user creates a new task by entering a title. The task appears in their task list immediately.

**Why this priority**: Task creation is the core value proposition of the application.

**Independent Test**: Can be tested by signing in, entering a task title, clicking "Add", and verifying the task appears in the list.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the dashboard, **When** they enter a task title and click "Add", **Then** the task is created via the API and appears in the task list.
2. **Given** an authenticated user, **When** they submit an empty title, **Then** the task is not created (empty input prevented).
3. **Given** the backend is unavailable, **When** the user tries to create a task, **Then** an error is displayed.

---

### User Story 4 - View Task List (Priority: P1)

An authenticated user sees all their tasks on the dashboard, ordered by creation time.

**Why this priority**: Viewing tasks is fundamental to the todo experience.

**Independent Test**: Can be tested by creating several tasks and verifying they all appear in the list on page load.

**Acceptance Scenarios**:

1. **Given** an authenticated user with tasks, **When** the dashboard loads, **Then** all their tasks are fetched and displayed.
2. **Given** an authenticated user with no tasks, **When** the dashboard loads, **Then** a "No tasks yet" message is displayed.
3. **Given** user A is authenticated, **When** the dashboard loads, **Then** only user A's tasks are shown (not user B's).

---

### User Story 5 - Toggle Task Completion (Priority: P2)

An authenticated user marks a task as complete or incomplete by clicking a checkbox or button.

**Why this priority**: Completing tasks is core to task management but secondary to creation and viewing.

**Independent Test**: Can be tested by clicking the complete toggle on a task and verifying the visual state changes and the API confirms the update.

**Acceptance Scenarios**:

1. **Given** an incomplete task, **When** the user clicks the complete button, **Then** the task is marked as completed (strikethrough text, checkmark visible).
2. **Given** a completed task, **When** the user clicks the complete button again, **Then** the task is marked as incomplete.

---

### User Story 6 - Delete a Task (Priority: P2)

An authenticated user deletes a task they no longer need.

**Why this priority**: Cleanup is important but secondary to core CRUD.

**Independent Test**: Can be tested by clicking delete on a task and verifying it disappears from the list.

**Acceptance Scenarios**:

1. **Given** a task exists in the list, **When** the user clicks "Delete", **Then** the task is removed from the backend and disappears from the UI.
2. **Given** a user tries to delete another user's task, **When** the API request is sent, **Then** a 403 Forbidden is returned.

---

### User Story 7 - Update a Task (Priority: P3)

An authenticated user edits the title or description of an existing task.

**Why this priority**: Editing is useful but less critical than creating and completing tasks.

**Independent Test**: Can be tested by modifying a task's title via PUT request and verifying the change persists.

**Acceptance Scenarios**:

1. **Given** an existing task, **When** the user updates its title, **Then** the updated title is persisted and displayed.

---

### Edge Cases

- What happens when the JWT token expires mid-session? The API returns 401/403, and the frontend should redirect to sign-in.
- What happens when the backend is unreachable? The frontend displays an error message; no data is lost.
- What happens when two users try to access each other's tasks? The backend validates `user_id` from the JWT `sub` claim against the URL parameter and returns 403 on mismatch.
- What happens when Neon PostgreSQL drops idle connections? The backend uses `pool_pre_ping=True` and `pool_recycle=300` to recover transparently.
- What happens when the JWKS endpoint is unreachable? Backend JWT verification fails, returning 401 to the client.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to register with name, email, and password via Better Auth.
- **FR-002**: System MUST authenticate users via email/password sign-in and issue JWT tokens.
- **FR-003**: System MUST protect all task API endpoints with JWT Bearer token authentication.
- **FR-004**: System MUST validate that the authenticated user (JWT `sub`) matches the `user_id` in API URL paths.
- **FR-005**: System MUST support full CRUD operations on tasks: Create, Read (list), Update, Delete.
- **FR-006**: System MUST support toggling task completion status via a dedicated PATCH endpoint.
- **FR-007**: System MUST persist all data in Neon PostgreSQL with connection pooling and pre-ping enabled.
- **FR-008**: System MUST redirect unauthenticated users to the sign-in page on the frontend.
- **FR-009**: System MUST allow users to sign out, destroying their session.
- **FR-010**: Backend MUST serve CORS-enabled responses allowing the frontend origin (`http://localhost:3000`).
- **FR-011**: Backend MUST auto-create database tables on startup via SQLModel metadata.
- **FR-012**: Frontend MUST use Better Auth's JWT plugin to obtain tokens for API requests.

### Key Entities

- **User**: Managed by Better Auth. Key attributes: `id` (UUID string), `name`, `email`, `emailVerified`, `image`, `createdAt`, `updatedAt`. Stored in `user` table (camelCase columns per Better Auth convention).
- **Session**: Managed by Better Auth. Tracks active user sessions with `token`, `expiresAt`, `userId`.
- **Account**: Managed by Better Auth. Links auth providers (credential) to users.
- **JWKS**: Managed by Better Auth. Stores EdDSA key pairs for JWT signing/verification.
- **Task**: Application entity. Key attributes: `id` (auto-increment int), `user_id` (string, FK to user), `title`, `description`, `completed` (boolean), `created_at`, `updated_at`. Stored in `tasks` table (snake_case columns).

## Technical Architecture

### Monorepo Structure

```
hackathon-2/
├── frontend/              # Next.js 15 (App Router, TypeScript, Tailwind CSS)
│   ├── src/
│   │   ├── app/           # Pages: /, /sign-up, /sign-in, /api/auth/[...all]
│   │   ├── components/    # React components
│   │   ├── lib/           # auth.ts, auth-client.ts, api.ts
│   │   └── types/         # task.ts
│   ├── .env.local         # Environment variables
│   └── package.json
├── backend/               # FastAPI + SQLModel
│   ├── app/
│   │   ├── main.py        # FastAPI entry, CORS, lifespan
│   │   ├── models.py      # Task SQLModel
│   │   ├── db.py          # Engine, session factory
│   │   ├── auth.py        # JWKS-based JWT verification
│   │   ├── schemas.py     # Pydantic request/response schemas
│   │   └── routes/
│   │       └── tasks.py   # Task CRUD endpoints
│   ├── .env               # Environment variables
│   └── requirements.txt
└── specs/                 # Specifications
```

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend Framework | Next.js | 15 (App Router) | SSR/CSR React framework |
| Frontend Language | TypeScript | 5.x | Type safety |
| Frontend Styling | Tailwind CSS | 4.x | Utility-first CSS |
| Auth Library | Better Auth | latest | Email/password auth + JWT |
| Backend Framework | FastAPI | latest | Python REST API |
| Backend ORM | SQLModel | latest | SQL + Pydantic models |
| Database | Neon PostgreSQL | serverless | Managed cloud Postgres |
| JWT Verification | PyJWT + PyJWKClient | latest | EdDSA JWKS-based verification |

### Authentication Flow

```
1. User submits credentials → Better Auth (frontend, port 3000)
2. Better Auth creates session → issues JWT (EdDSA signed)
3. Frontend calls authClient.token() → receives JWT string
4. Frontend sends API request with Authorization: Bearer <JWT>
5. FastAPI backend receives request
6. auth.py fetches JWKS from http://localhost:3000/api/auth/jwks
7. PyJWKClient extracts signing key, PyJWT verifies token
8. Backend extracts user_id from JWT "sub" claim
9. Route handler validates URL user_id matches JWT sub
10. Query executes with user ownership filter
```

### API Contract

**Base URL**: `http://localhost:8000/api`

| Method | Endpoint | Auth | Request Body | Response | Status |
|--------|----------|------|-------------|----------|--------|
| GET | `/{user_id}/tasks` | Bearer JWT | - | `Task[]` | 200 |
| POST | `/{user_id}/tasks` | Bearer JWT | `{ title, description? }` | `Task` | 201 |
| GET | `/{user_id}/tasks/{id}` | Bearer JWT | - | `Task` | 200 |
| PUT | `/{user_id}/tasks/{id}` | Bearer JWT | `{ title?, description?, completed? }` | `Task` | 200 |
| DELETE | `/{user_id}/tasks/{id}` | Bearer JWT | - | - | 204 |
| PATCH | `/{user_id}/tasks/{id}/complete` | Bearer JWT | - | `Task` | 200 |
| GET | `/` | None | - | `{ app, version, docs }` | 200 |
| GET | `/health` | None | - | `{ status }` | 200 |

**Error Responses**:
- `403 Forbidden` - Missing/invalid JWT or user_id mismatch
- `404 Not Found` - Task does not exist or belongs to another user
- `422 Unprocessable Entity` - Invalid request body

### Database Schema

**Better Auth tables** (managed by Better Auth, camelCase):
- `user` (id, name, email, emailVerified, image, createdAt, updatedAt)
- `session` (id, expiresAt, token, createdAt, updatedAt, ipAddress, userAgent, userId)
- `account` (id, accountId, providerId, userId, ...)
- `verification` (id, identifier, value, expiresAt, createdAt, updatedAt)
- `jwks` (id, publicKey, privateKey, createdAt)

**Application tables** (managed by SQLModel, snake_case):
- `tasks` (id, user_id, title, description, completed, created_at, updated_at)

### Environment Configuration

**Frontend** (`.env.local`):
- `BETTER_AUTH_SECRET` - Shared secret for Better Auth
- `BETTER_AUTH_URL` - Better Auth base URL (http://localhost:3000)
- `DATABASE_URL` - Neon PostgreSQL connection string (for Better Auth adapter)
- `NEXT_PUBLIC_API_URL` - Backend API URL (http://localhost:8000)
- `NEXT_PUBLIC_BETTER_AUTH_URL` - Public Better Auth URL

**Backend** (`.env`):
- `DATABASE_URL` - Neon PostgreSQL connection string (for SQLModel)
- `BETTER_AUTH_SECRET` - Shared secret (for reference; JWKS used for verification)
- `JWKS_URL` - JWKS endpoint (defaults to http://localhost:3000/api/auth/jwks)

### Key Implementation Details

1. **Neon PostgreSQL Connection Handling**: Uses `pool_pre_ping=True` and `pool_recycle=300` on the SQLAlchemy engine to handle Neon's serverless connection drops gracefully.

2. **Better Auth Database Adapter**: Requires a `pg.Pool` instance passed directly as the `database` option (not a `{ type, url }` config object).

3. **JWT Algorithm**: Better Auth uses EdDSA asymmetric signing (not HS256). Backend verifies via JWKS public keys, not shared secret.

4. **Token Extraction Pattern**: Frontend uses `authClient.token()` which returns `{ data: { token: string } }`. The token is extracted as `(res as { data?: { token?: string } })?.data?.token`.

5. **Owner Validation**: Every task route validates that the JWT `sub` claim matches the `user_id` URL parameter. Mismatch returns 403.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can register, sign in, and sign out without errors.
- **SC-002**: Authenticated users can create, list, update, delete, and toggle-complete tasks.
- **SC-003**: Unauthenticated API requests receive 403 Forbidden responses.
- **SC-004**: Users cannot access or modify other users' tasks (returns 403).
- **SC-005**: All E2E tests pass: sign-up, sign-in, JWT fetch, create (201), list (200), toggle (200), update (200), delete (204), auth rejection (403).
- **SC-006**: Backend recovers from Neon connection drops without manual intervention.
- **SC-007**: Frontend properly redirects unauthenticated users to `/sign-in`.
