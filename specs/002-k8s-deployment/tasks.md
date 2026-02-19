# Tasks: Kubernetes Deployment

**Input**: Design documents from `/specs/002-k8s-deployment/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: No automated tests — this feature uses manual validation checkpoints (docker compose up, kubectl apply).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration changes and ignore files needed before any containerization work

- [x] T001 [P] Update Next.js config to enable standalone output mode in `frontend/next.config.ts` — set `output: "standalone"` inside the `nextConfig` object
- [x] T002 [P] Create backend Docker ignore file at `backend/.dockerignore` — exclude `.env`, `.env.*`, `__pycache__`, `*.pyc`, `.git`, `.gitignore`, `venv/`, `.venv/`, `*.egg-info`, `tests/`
- [x] T003 [P] Create frontend Docker ignore file at `frontend/.dockerignore` — exclude `node_modules`, `.env.local`, `.env`, `.next`, `.git`, `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Application code changes that MUST be complete before containerized deployment works correctly

**⚠️ CRITICAL**: CORS must be updated before k8s Ingress routing will function

- [x] T004 Update CORS configuration in `backend/app/main.py` — add `"http://taskflow.local"` to `allow_origins` list and add support for `CORS_ORIGIN` environment variable (read via `os.environ.get("CORS_ORIGIN", "")`, filter empty strings from the origins list). Add `import os` at top of file if not already present.

**Checkpoint**: Application code changes complete — containerization can begin

---

## Phase 3: User Story 1 — Containerized Application Runs Locally (Priority: P1) 🎯 MVP

**Goal**: Developer runs `docker compose up --build` and both backend + frontend containers start, with all application features (auth, tasks, chat) working end-to-end.

**Independent Test**: Run `docker compose up --build`, open http://localhost:3000, register a user, create tasks, use AI chatbot. Stop with `docker compose down`.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create backend Dockerfile at `backend/Dockerfile` — multi-stage build: Stage 1 (builder) uses `python:3.12-slim-bookworm`, creates virtualenv, copies `requirements.txt` first then installs deps, copies `app/` directory. Stage 2 (runtime) uses `python:3.12-slim-bookworm`, copies virtualenv from builder, copies `app/` directory, creates non-root user `appuser` (useradd --create-home), sets WORKDIR to `/home/appuser`, exposes port 8000, runs as `appuser`, CMD `["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- [x] T006 [P] [US1] Create frontend Dockerfile at `frontend/Dockerfile` — three-stage build: Stage 1 (deps) uses `node:20-alpine`, copies `package.json` and `package-lock.json`, runs `npm ci`. Stage 2 (builder) copies all source, accepts `ARG NEXT_PUBLIC_API_URL=http://localhost:8000`, sets it as ENV, runs `npm run build`. Stage 3 (runtime) uses `node:20-alpine`, creates non-root user `nextjs` (addgroup/adduser), copies `.next/standalone` from builder, copies `.next/static` from builder to `.next/static`, copies `public/` from builder if it exists, exposes port 3000, sets ENV `HOSTNAME="0.0.0.0"`, runs as `nextjs`, CMD `["node", "server.js"]`
- [x] T007 [US1] Create Docker Compose config at `compose.yaml` (repo root) — define two services: `backend` (build: `./backend`, ports: `8000:8000`, env_file: `./backend/.env`) and `frontend` (build context: `./frontend`, build args: `NEXT_PUBLIC_API_URL=http://localhost:8000`, ports: `3000:3000`, env_file: `./frontend/.env.local`, depends_on: `backend`). Use Docker Compose V2 format (no `version:` key).

**Checkpoint**: Run `docker compose up --build` — both containers start, app accessible at http://localhost:3000, all features work. Backend image under 200MB, frontend image under 500MB. Run `docker compose down` to verify clean shutdown. Inspect images to confirm no `.env` files or secrets baked in.

---

## Phase 4: User Story 2 — Application Deploys to Kubernetes (Priority: P1)

**Goal**: Engineer applies k8s manifests to a cluster and the application is accessible via `http://taskflow.local` with correct path-based routing (frontend at `/`, backend at `/api`).

**Independent Test**: Start Minikube, enable ingress addon, build images into Minikube's Docker daemon, create secrets via kubectl, run `kubectl apply -f k8s/`, add `/etc/hosts` entry, access http://taskflow.local and verify all features work.

### Implementation for User Story 2

- [x] T008 [P] [US2] Create Kubernetes namespace manifest at `k8s/namespace.yaml` — define namespace `taskflow`
- [x] T009 [P] [US2] Create Kubernetes ConfigMap at `k8s/configmap.yaml` — name `taskflow-config` in namespace `taskflow`, data: `AI_PROVIDER: "openai"`, `CORS_ORIGIN: "http://taskflow.local"`
- [x] T010 [P] [US2] Create Kubernetes Secrets template at `k8s/secrets-template.yaml` — name `taskflow-secrets` in namespace `taskflow`, include placeholder values for `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `BETTER_AUTH_SECRET` with comments explaining to create real secrets via `kubectl create secret generic` command. Add a comment at top: "DO NOT apply this file directly. Use kubectl create secret generic instead."
- [x] T011 [US2] Create backend Deployment and Service manifest at `k8s/backend-deployment.yaml` — Deployment: name `taskflow-backend`, namespace `taskflow`, 2 replicas, selector and labels `app: taskflow-backend`, container image `taskflow-backend:latest`, `imagePullPolicy: IfNotPresent`, port 8000, resources (requests: cpu 100m, memory 128Mi; limits: cpu 500m, memory 256Mi), liveness probe (httpGet `/health` port 8000, initialDelaySeconds 10, periodSeconds 30), readiness probe (httpGet `/health` port 8000, initialDelaySeconds 5, periodSeconds 10), envFrom referencing Secret `taskflow-secrets` and ConfigMap `taskflow-config`, strategy RollingUpdate (maxSurge 1, maxUnavailable 0). Service: name `taskflow-backend`, namespace `taskflow`, type ClusterIP, port 8000 targetPort 8000, selector `app: taskflow-backend`.
- [x] T012 [US2] Create frontend Deployment and Service manifest at `k8s/frontend-deployment.yaml` — Deployment: name `taskflow-frontend`, namespace `taskflow`, 1 replica, selector and labels `app: taskflow-frontend`, container image `taskflow-frontend:latest`, `imagePullPolicy: IfNotPresent`, port 3000, resources (requests: cpu 100m, memory 128Mi; limits: cpu 250m, memory 256Mi), liveness probe (tcpSocket port 3000, initialDelaySeconds 10, periodSeconds 30), strategy RollingUpdate (maxSurge 1, maxUnavailable 0). Service: name `taskflow-frontend`, namespace `taskflow`, type ClusterIP, port 80 targetPort 3000, selector `app: taskflow-frontend`.
- [x] T013 [US2] Create Ingress manifest at `k8s/ingress.yaml` — name `taskflow-ingress`, namespace `taskflow`, annotation `kubernetes.io/ingress.class: nginx`, spec rules: host `taskflow.local`, paths: `/api` pathType Prefix backend service `taskflow-backend` port 8000, `/` pathType Prefix backend service `taskflow-frontend` port 80. Backend FastAPI routes already include `/api/` prefix so no path rewriting is needed.

**Checkpoint**: On Minikube — `eval $(minikube docker-env)`, build images, `kubectl create secret generic taskflow-secrets --namespace taskflow ...`, `kubectl apply -f k8s/`, `echo "$(minikube ip) taskflow.local" | sudo tee -a /etc/hosts`. All pods reach Ready state. Access http://taskflow.local — frontend loads, API calls to `/api/...` reach backend. Health checks pass.

---

## Phase 5: User Story 3 — Self-Healing and Autoscaling (Priority: P2)

**Goal**: Backend automatically recovers from pod termination and scales from 2 to 5 replicas when CPU exceeds 70%.

**Independent Test**: Delete a backend pod with `kubectl delete pod`, verify replacement starts and app stays available. Generate CPU load and verify HPA scales up replicas.

### Implementation for User Story 3

- [x] T014 [US3] Create HPA manifest at `k8s/hpa.yaml` — name `taskflow-backend-hpa`, namespace `taskflow`, scaleTargetRef apiVersion `apps/v1` kind `Deployment` name `taskflow-backend`, minReplicas 2, maxReplicas 5, metrics: resource cpu type Utilization averageUtilization 70

**Checkpoint**: Verify self-healing: `kubectl delete pod <backend-pod> -n taskflow` — replacement starts within seconds, app remains accessible. Verify HPA: `kubectl get hpa -n taskflow` shows TARGETS column with current/target CPU values (not `<unknown>` — requires metrics-server addon). Note: Autoscaling trigger test requires CPU load generation which is a manual validation step.

---

## Phase 6: User Story 4 — Image Build and Push Workflow (Priority: P2)

**Goal**: Developer can build, tag, and push container images to a registry with version-based tags for reproducible deployments and rollbacks.

**Independent Test**: Build images with a git SHA tag, push to GHCR (or local registry), update k8s deployment to reference the tagged image, verify the correct version runs.

### Implementation for User Story 4

- [x] T015 [US4] Update `compose.yaml` to add image names with configurable tags — add `image: taskflow-backend:${TAG:-latest}` and `image: taskflow-frontend:${TAG:-latest}` to each service so `TAG=v1.0.0 docker compose build` produces tagged images
- [x] T016 [US4] Update `k8s/backend-deployment.yaml` to add comment documenting image tag update procedure — add comment block showing how to update the image field for registry-based deployments: `image: ghcr.io/<owner>/taskflow-backend:<tag>` and the `kubectl set image` command for rolling updates
- [x] T017 [US4] Update `k8s/frontend-deployment.yaml` to add comment documenting image tag update procedure — same pattern as T016 for frontend image

**Checkpoint**: Build images with `TAG=$(git rev-parse --short HEAD) docker compose build`, verify images are tagged correctly with `docker images | grep taskflow`. If GHCR credentials are configured, push with `docker push ghcr.io/<owner>/taskflow-backend:<tag>`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation across all user stories

- [x] T018 [P] Validate quickstart.md instructions end-to-end — follow `specs/002-k8s-deployment/quickstart.md` steps for both Docker Compose and Kubernetes deployment paths, fix any incorrect commands or missing steps
- [x] T019 [P] Verify no secrets in committed files — scan all new files (`backend/Dockerfile`, `frontend/Dockerfile`, `compose.yaml`, `k8s/*.yaml`) for hardcoded secrets, API keys, or credentials. Confirm `.dockerignore` files exclude `.env` files. Confirm `k8s/secrets-template.yaml` has only placeholder values.
- [x] T020 Verify container image sizes — build both images and check sizes: backend should be under 200MB, frontend under 500MB. If over limit, investigate and optimize Dockerfile layers.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002, T003 can all run in parallel immediately
- **Foundational (Phase 2)**: T004 has no dependencies on Phase 1 — can run in parallel with Setup
- **US1 (Phase 3)**: Depends on Setup (T001-T003) for Dockerfiles to work correctly — T005 and T006 can run in parallel
- **US2 (Phase 4)**: Depends on US1 (T005-T006 for built images) and T004 (CORS update) — T008, T009, T010 can run in parallel; T011, T012 depend on T009/T010; T013 depends on T011/T012
- **US3 (Phase 5)**: Depends on US2 (T011 for backend deployment to exist) — single task T014
- **US4 (Phase 6)**: Depends on US1 (T007 for compose.yaml) and US2 (T011/T012 for k8s manifests) — T015, T016, T017 can run in parallel
- **Polish (Phase 7)**: Depends on all previous phases — T018, T019, T020 can run in parallel

### Within Each User Story

- US1: T005 ∥ T006, then T007 (needs both Dockerfiles)
- US2: T008 ∥ T009 ∥ T010, then T011 ∥ T012, then T013 (needs both services)
- US3: Single task T014
- US4: T015 ∥ T016 ∥ T017

### Parallel Opportunities

- **Phase 1**: T001 ∥ T002 ∥ T003 (3 parallel tasks)
- **Phase 1 + Phase 2**: T001 ∥ T002 ∥ T003 ∥ T004 (4 parallel tasks — all independent)
- **Phase 3**: T005 ∥ T006 (2 parallel tasks)
- **Phase 4 first batch**: T008 ∥ T009 ∥ T010 (3 parallel tasks)
- **Phase 4 second batch**: T011 ∥ T012 (2 parallel tasks)
- **Phase 6**: T015 ∥ T016 ∥ T017 (3 parallel tasks)
- **Phase 7**: T018 ∥ T019 ∥ T020 (3 parallel tasks)

---

## Parallel Example: User Story 2 (Kubernetes Deployment)

```bash
# Batch 1 — Launch namespace, configmap, and secrets template in parallel:
Task: "Create namespace manifest at k8s/namespace.yaml"
Task: "Create ConfigMap at k8s/configmap.yaml"
Task: "Create secrets template at k8s/secrets-template.yaml"

# Batch 2 — Launch backend and frontend deployments in parallel:
Task: "Create backend Deployment+Service at k8s/backend-deployment.yaml"
Task: "Create frontend Deployment+Service at k8s/frontend-deployment.yaml"

# Batch 3 — Ingress depends on both services:
Task: "Create Ingress at k8s/ingress.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Docker Compose)

1. Complete Phase 1: Setup (T001-T003) — parallel
2. Complete Phase 2: Foundational (T004) — parallel with Phase 1
3. Complete Phase 3: US1 (T005-T007)
4. **STOP and VALIDATE**: `docker compose up --build` — app works at localhost
5. This alone delivers containerization value (reproducible builds)

### Full Delivery (All User Stories)

1. Complete Setup + Foundational (T001-T004)
2. Complete US1: Docker Compose (T005-T007) → Validate locally
3. Complete US2: Kubernetes (T008-T013) → Validate on Minikube
4. Complete US3: HPA (T014) → Validate autoscaler
5. Complete US4: Image workflow (T015-T017) → Validate tagging
6. Polish (T018-T020) → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature has NO automated tests — validation is manual (docker compose up, kubectl apply, browser testing)
- Commit after each phase completion
- Backend image target: <200MB; Frontend image target: <500MB
- All secrets managed via k8s Secrets or .env files (never in images or VCS)
- Database (Neon PostgreSQL) remains external — no k8s database deployment
