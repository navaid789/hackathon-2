# Implementation Plan: Kubernetes Deployment

**Branch**: `002-k8s-deployment` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-k8s-deployment/spec.md`

## Summary

Containerize the TaskFlow application (FastAPI backend + Next.js frontend) with Docker and deploy to Kubernetes. The backend uses `python:3.12-slim-bookworm` with multi-stage builds; the frontend uses `node:20-alpine` with Next.js standalone output. Local development uses Docker Compose; Kubernetes deployment uses plain YAML manifests with Ingress (NGINX), Secrets, ConfigMaps, and HPA. Database remains on external Neon PostgreSQL.

## Technical Context

**Language/Version**: Python 3.12 (backend), Node.js 20 (frontend), YAML (manifests)
**Primary Dependencies**: Docker, Docker Compose V2, Kubernetes 1.28+, Minikube, NGINX Ingress Controller
**Storage**: External Neon PostgreSQL (no changes)
**Testing**: Manual validation — `docker compose up`, `kubectl apply`, functional tests via browser
**Target Platform**: Linux containers on Kubernetes (local Minikube for dev, any k8s cluster for production)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Backend image <200MB, frontend image <500MB, pod ready <60s
**Constraints**: No secrets in images or VCS; non-root containers; rolling update with zero downtime
**Scale/Scope**: 2-5 backend replicas (HPA), 1 frontend replica

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is not yet configured (template only). No gates to validate. Proceeding with industry best practices:

- Smallest viable diff: Only adding infrastructure files (Dockerfiles, compose.yaml, k8s/ manifests). Minimal application code changes (next.config.ts output mode, CORS update).
- No secrets in code: All sensitive values in k8s Secrets or `.env` files (gitignored).
- No unnecessary complexity: Plain YAML manifests instead of Helm charts. No CI/CD pipeline (hackathon scope).

## Project Structure

### Documentation (this feature)

```text
specs/002-k8s-deployment/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Infrastructure entity definitions
├── quickstart.md        # Setup and deployment guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (new files)

```text
hackathon-2/
├── backend/
│   ├── Dockerfile              # NEW — Multi-stage Python build
│   └── .dockerignore           # NEW — Exclude .env, __pycache__, .git
├── frontend/
│   ├── Dockerfile              # NEW — Multi-stage Node.js build
│   └── .dockerignore           # NEW — Exclude node_modules, .env.local, .git
├── compose.yaml                # NEW — Local Docker Compose orchestration
├── k8s/                        # NEW — Kubernetes manifests directory
│   ├── namespace.yaml          # NEW — Optional namespace isolation
│   ├── backend-deployment.yaml # NEW — Backend Deployment + Service
│   ├── frontend-deployment.yaml# NEW — Frontend Deployment + Service
│   ├── configmap.yaml          # NEW — Non-sensitive configuration
│   ├── secrets-template.yaml   # NEW — Secret template (placeholder values)
│   ├── ingress.yaml            # NEW — NGINX Ingress routing rules
│   └── hpa.yaml                # NEW — Horizontal Pod Autoscaler for backend
└── .dockerignore               # NEW — Root-level ignore (if needed)
```

### Existing Files Modified

```text
frontend/next.config.ts          # MODIFIED — Add output: "standalone"
backend/app/main.py              # MODIFIED — Update CORS origins to include k8s domain
```

**Structure Decision**: Infrastructure-only additions alongside the existing web application structure. All k8s manifests live in a single `k8s/` directory at the repo root for simple `kubectl apply -f k8s/` deployment.

## Complexity Tracking

No constitution violations to justify — all additions are standard infrastructure patterns.

---

## Phase 0: Research (Complete)

See [research.md](./research.md) for full findings. Key decisions:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Container registry | GHCR (+ `minikube docker-env` for local) | Free with GitHub, no extra accounts |
| Python base image | `python:3.12-slim-bookworm` | `psycopg2-binary` requires glibc (Alpine breaks) |
| Node.js base image | `node:20-alpine` | Smallest viable; no glibc dependencies |
| Ingress controller | NGINX Ingress (Minikube addon) | One command setup |
| Readiness probe | Shallow `/health` check (no DB check) | Prevents cascading failures |
| Compose file | `compose.yaml` (V2 canonical) | Docker Compose V1 is deprecated |
| `NEXT_PUBLIC_*` vars | Build-time ARG | Inlined into JS bundle at build time |
| HPA metrics | `minikube addons enable metrics-server` | Required; not enabled by default |

---

## Phase 1: Design

### 1.1 Backend Dockerfile Design

**Strategy**: Two-stage build

**Stage 1 — Builder**:
- Base: `python:3.12-slim-bookworm`
- Install dependencies into a virtualenv
- Copy only `requirements.txt` first (cache layer)
- Then copy application code

**Stage 2 — Runtime**:
- Base: `python:3.12-slim-bookworm`
- Copy virtualenv from builder
- Copy application code (`app/` directory)
- Create non-root user `appuser`
- Expose port 8000
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- HEALTHCHECK: `curl -f http://localhost:8000/health || exit 1`

**Expected image size**: ~150-180MB

### 1.2 Frontend Dockerfile Design

**Strategy**: Three-stage build

**Stage 1 — Dependencies**:
- Base: `node:20-alpine`
- Copy `package.json` and `package-lock.json`
- Run `npm ci` (deterministic install)

**Stage 2 — Builder**:
- Copy source code
- Accept `NEXT_PUBLIC_API_URL` as build ARG
- Run `npm run build`

**Stage 3 — Runtime**:
- Base: `node:20-alpine`
- Copy `.next/standalone`, `.next/static`, `public/`
- Create non-root user `nextjs`
- Expose port 3000
- CMD: `node server.js`

**Expected image size**: ~150-200MB

### 1.3 Docker Compose Design

```yaml
# compose.yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    depends_on: []  # DB is external

  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    ports: ["3000:3000"]
    env_file: ./frontend/.env.local
    depends_on: [backend]
```

### 1.4 Kubernetes Manifest Design

**Namespace**: `taskflow` (optional, keeps resources isolated)

**Backend Deployment** (`k8s/backend-deployment.yaml`):
- 2 replicas
- Image: `taskflow-backend:latest` (overridden for registry deployments)
- Resources: 100m/128Mi request, 500m/256Mi limit
- Liveness probe: GET `/health`, period 30s, initial delay 10s
- Readiness probe: GET `/health`, period 10s, initial delay 5s
- Env from: `taskflow-secrets` (Secret), `taskflow-config` (ConfigMap)
- Rolling update: maxSurge 1, maxUnavailable 0
- Includes ClusterIP Service on port 8000

**Frontend Deployment** (`k8s/frontend-deployment.yaml`):
- 1 replica
- Image: `taskflow-frontend:latest`
- Resources: 100m/128Mi request, 250m/256Mi limit
- Liveness probe: TCP socket 3000
- Rolling update: maxSurge 1, maxUnavailable 0
- Includes ClusterIP Service on port 80 → 3000

**Ingress** (`k8s/ingress.yaml`):
- Host: `taskflow.local`
- NGINX Ingress class
- Rules:
  - Path `/api` → `taskflow-backend:8000` (Prefix match)
  - Path `/` → `taskflow-frontend:80` (Prefix match)
- Note: Backend routes already have `/api/` prefix in the FastAPI routes, so no path rewriting needed. The Ingress passes the full path through.

**Secrets Template** (`k8s/secrets-template.yaml`):
- Placeholder values with comments explaining how to create real secrets via `kubectl create secret`
- NOT applied directly — serves as documentation

**ConfigMap** (`k8s/configmap.yaml`):
- `AI_PROVIDER: openai`

**HPA** (`k8s/hpa.yaml`):
- Target: `taskflow-backend` deployment
- Min: 2, Max: 5
- Metric: CPU at 70% average utilization

### 1.5 Application Code Changes

**`frontend/next.config.ts`**:
```typescript
const nextConfig: NextConfig = {
  output: "standalone",
};
```

**`backend/app/main.py`** — Update CORS:
```python
allow_origins=[
    "http://localhost:3000",
    "http://taskflow.local",
    os.environ.get("CORS_ORIGIN", ""),
]
```
Filter empty strings. Add `CORS_ORIGIN` to ConfigMap so it's configurable per environment.

### 1.6 .dockerignore Files

**`backend/.dockerignore`**:
```
.env
.env.*
__pycache__
*.pyc
.git
.gitignore
venv/
.venv/
*.egg-info
tests/
```

**`frontend/.dockerignore`**:
```
node_modules
.env.local
.env
.next
.git
.gitignore
```

---

## Implementation Order

| Phase | What | Files | Depends On |
|-------|------|-------|------------|
| 1 | Next.js standalone config | `frontend/next.config.ts` | Nothing |
| 2 | Backend Dockerfile + .dockerignore | `backend/Dockerfile`, `backend/.dockerignore` | Nothing |
| 3 | Frontend Dockerfile + .dockerignore | `frontend/Dockerfile`, `frontend/.dockerignore` | Phase 1 |
| 4 | Docker Compose | `compose.yaml` | Phase 2, 3 |
| 5 | **VALIDATE**: `docker compose up --build` works | — | Phase 4 |
| 6 | CORS update | `backend/app/main.py` | Nothing |
| 7 | K8s ConfigMap + Secrets template | `k8s/configmap.yaml`, `k8s/secrets-template.yaml` | Nothing |
| 8 | K8s Backend Deployment + Service | `k8s/backend-deployment.yaml` | Phase 7 |
| 9 | K8s Frontend Deployment + Service | `k8s/frontend-deployment.yaml` | Phase 7 |
| 10 | K8s Ingress | `k8s/ingress.yaml` | Phase 8, 9 |
| 11 | K8s HPA | `k8s/hpa.yaml` | Phase 8 |
| 12 | **VALIDATE**: `kubectl apply -f k8s/` on Minikube | — | Phase 7-11 |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `NEXT_PUBLIC_API_URL` baked at build time | Frontend image not portable across environments | Acceptable for hackathon; document limitation |
| Neon PostgreSQL connection limits | Multiple backend replicas may exhaust connection pool | Use `pool_pre_ping=True` (already set) and configure `pool_size` |
| NGINX Ingress retirement (March 2026) | Ingress controller may lose support | Use standard annotations; migration to Gateway API is straightforward |
| Metrics-server not installed | HPA shows `<unknown>`, never scales | Document addon requirement in quickstart |

---

## Follow-ups (Out of Scope)

- CI/CD pipeline for automated image build and deployment
- TLS/HTTPS on Ingress (cert-manager)
- Cloud-specific k8s deployment (EKS/GKE/AKS)
- Helm chart for templated configuration
- Runtime environment variable injection for Next.js (multi-environment support)
