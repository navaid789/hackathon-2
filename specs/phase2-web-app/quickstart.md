# Quickstart: Phase II - Full-Stack Todo Web Application

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm 10+
- Neon PostgreSQL account with a database provisioned

## 1. Clone and Navigate

```bash
cd hackathon-2
```

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Install dependencies
.venv/bin/pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://neondb_owner:<password>@<host>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
BETTER_AUTH_SECRET=<your-secret>
EOF
```

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << 'EOF'
BETTER_AUTH_SECRET=<your-secret>
BETTER_AUTH_URL=http://localhost:3000
DATABASE_URL=postgresql://neondb_owner:<password>@<host>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
EOF
```

## 4. Database Migrations

```bash
# Better Auth tables (from frontend directory)
cd frontend
DATABASE_URL="<your-connection-string>" npx @better-auth/cli migrate --yes

# Backend tables auto-create on startup (SQLModel)
```

## 5. Start Servers

```bash
# Terminal 1: Backend (port 8000)
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend (port 3000)
cd frontend && npm run dev
```

Or use the Claude Code skill: `/dev.start`

## 6. Verify

```bash
# Backend health
curl http://localhost:8000/health
# → {"status":"ok"}

# Frontend
open http://localhost:3000
```

## 7. Development Workflow

| Task | Command |
|------|---------|
| Start servers | `/dev.start` |
| Stop servers | `/dev.stop` |
| Run E2E tests | `/dev.test-e2e` |
| Run migrations | `/dev.db-migrate` |
| Add API endpoint | `/dev.add-route "GET /api/stats - return statistics"` |
| Add frontend page | `/dev.add-page "settings page for user preferences"` |

## Environment Variables Reference

| Variable | Location | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | backend/.env, frontend/.env.local | Neon PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | backend/.env, frontend/.env.local | Auth secret key |
| `BETTER_AUTH_URL` | frontend/.env.local | Better Auth base URL |
| `NEXT_PUBLIC_API_URL` | frontend/.env.local | Backend API URL (public) |
| `NEXT_PUBLIC_BETTER_AUTH_URL` | frontend/.env.local | Better Auth URL (public) |

## Important Notes

- Do NOT include `channel_binding=require` in DATABASE_URL
- Do NOT commit `.env` or `.env.local` files
- Backend uses EdDSA JWT verification via JWKS, not HS256
- Better Auth database config requires `pg.Pool` instance, not URL string
