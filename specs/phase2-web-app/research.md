# Research: Phase II - Full-Stack Todo Web Application

**Date**: 2026-01-29 | **Status**: Complete

## R-001: Better Auth JWT Signing Algorithm

**Question**: What JWT algorithm does Better Auth use, and how should the backend verify tokens?

**Finding**: Better Auth uses **EdDSA** (Edwards-curve Digital Signature Algorithm) for JWT signing by default. It auto-generates key pairs stored in the `jwks` table in the database. Tokens are signed with the private key and can be verified using the public key exposed via a standard JWKS endpoint.

**Decision**: Use `PyJWT` with `PyJWKClient` on the backend to fetch public keys from `http://localhost:3000/api/auth/jwks`. Accept algorithms: `["EdDSA", "ES256", "RS256", "PS256"]`.

**Alternatives Rejected**:
- HS256 with shared secret: Better Auth does not sign JWTs with `BETTER_AUTH_SECRET`; it uses asymmetric EdDSA keys
- `python-jose` library: Less mature JWKS client support compared to `PyJWT`

**Evidence**: Backend auth.py implementation verified working in E2E tests.

---

## R-002: Better Auth Database Adapter Configuration

**Question**: How should Better Auth connect to PostgreSQL?

**Finding**: Better Auth's internal Kysely database adapter requires a **`pg.Pool` instance** passed directly as the `database` configuration option. It does NOT accept a `{ type: "postgres", url: "..." }` configuration object.

**Decision**: Create a `pg.Pool` instance with the connection string and pass it directly:
```typescript
import { Pool } from "pg";
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const auth = betterAuth({ database: pool, ... });
```

**Alternatives Rejected**:
- `{ type: "postgres", url }` config: Fails with "Failed to initialize database adapter"
- Prisma adapter: Unnecessary complexity for this use case

**Evidence**: Frontend auth.ts working with pg.Pool.

---

## R-003: Neon PostgreSQL Connection Stability

**Question**: How to handle Neon's serverless connection drops?

**Finding**: Neon PostgreSQL uses a serverless architecture that automatically suspends idle connections after a period of inactivity. This causes "SSL connection has been closed unexpectedly" errors in long-running application servers.

**Decision**: Configure SQLAlchemy engine with:
- `pool_pre_ping=True` — tests connections before use, discards stale ones
- `pool_recycle=300` — recycles connections every 5 minutes

**Additional**: Remove `channel_binding=require` from connection strings, as it causes compatibility issues with the `pg` Node.js library and some Python drivers.

**Alternatives Rejected**:
- Manual reconnect logic: Over-engineered for this use case
- No mitigation: Causes intermittent 500 errors

**Evidence**: Backend stable through multiple idle periods after applying fixes.

---

## R-004: Better Auth Token API Shape

**Question**: How does the frontend obtain JWT tokens from Better Auth?

**Finding**: The `jwtClient` plugin adds a `.token()` method to the auth client. This method returns a response envelope: `{ data: { token: string } }`, not a raw string.

**Decision**: Extract token using type assertion:
```typescript
const res = await authClient.token();
const jwt = (res as { data?: { token?: string } })?.data?.token;
```

**Alternatives Rejected**:
- `authClient.getToken()`: Method does not exist on the client
- Direct `res.data.token` access: TypeScript type errors without assertion
- `authClient.$fetch("/api/auth/token")`: Unnecessary manual fetch

**Evidence**: Token extraction working in page.tsx `getToken()` helper.

---

## R-005: Database Migration Strategy

**Question**: How to manage schema across two systems (Better Auth + SQLModel)?

**Finding**: Better Auth and SQLModel manage separate sets of tables. Better Auth has its own CLI migration tool; SQLModel uses `metadata.create_all()`.

**Decision**: Two-track migration:
1. **Better Auth tables**: `npx @better-auth/cli migrate --yes` (from frontend directory with DATABASE_URL set)
2. **Application tables**: Automatic via `SQLModel.metadata.create_all(engine)` in FastAPI lifespan

**Key Schema Notes**:
- Better Auth uses **camelCase** column names (e.g., `emailVerified`, `createdAt`)
- SQLModel/backend uses **snake_case** column names (e.g., `user_id`, `created_at`)
- The legacy `user.hashed_password` column from Phase I must be nullable
- The legacy `user.created_at` column needs a default value

**Evidence**: Both migration paths verified working. Dev skill `dev.db-migrate` automates both.

---

## R-006: Frontend Framework Version

**Question**: Which Next.js version to use?

**Finding**: Next.js 16.1.5 is the latest stable release available. It includes App Router, Turbopack (dev server), and React 19.2.3 support.

**Decision**: Use Next.js 16.1.5 with App Router and Turbopack for development.

**Notes**: The constitution referenced "Next.js 16+" for future phases. The actual version installed (16.1.5) satisfies this.

---

## R-007: CORS Configuration

**Question**: What CORS settings are needed for the frontend-backend split?

**Finding**: The frontend (port 3000) makes cross-origin requests to the backend (port 8000). FastAPI's `CORSMiddleware` must explicitly allow the frontend origin.

**Decision**: Configure CORS in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: `allow_credentials=True` is required for cookie-based requests (though the primary auth mechanism is Bearer tokens).
