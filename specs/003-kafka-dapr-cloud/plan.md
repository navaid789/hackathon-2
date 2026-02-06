# Implementation Plan: Kafka + Dapr Cloud Deployment

**Branch**: `003-kafka-dapr-cloud` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-kafka-dapr-cloud/spec.md`

## Summary

Add event-driven architecture to the TaskFlow application using Apache Kafka as the message broker and Dapr as the distributed application runtime. Task CRUD operations publish CloudEvents to Kafka via Dapr sidecars. A new notification worker microservice consumes events to generate overdue alerts, daily summaries, and productivity analytics. Distributed tracing via Zipkin provides end-to-end observability. Local development uses Docker Compose; Kubernetes deployment uses plain YAML manifests with Dapr annotations.

## Technical Context

**Language/Version**: Python 3.12 (backend + worker), Node.js 20 (frontend), YAML (manifests)
**Primary Dependencies**: Apache Kafka 3.9.0 (KRaft), Dapr 1.14.x, Zipkin, Docker, Docker Compose V2, Kubernetes 1.28+, Minikube
**Storage**: External Neon PostgreSQL (shared by backend and worker — new tables for notifications + analytics)
**Testing**: Manual validation — Docker Compose up, kubectl apply, functional tests via browser and curl
**Target Platform**: Linux containers on Kubernetes (local Minikube for dev)
**Project Type**: Web application (backend + frontend + worker)
**Performance Goals**: Events published <2s, worker processing <5s, analytics API <1s, zero latency impact on task CRUD
**Constraints**: No secrets in images or VCS; non-root containers; at-least-once event delivery with idempotent processing
**Scale/Scope**: 2-5 backend replicas (existing HPA), 1 frontend replica, 1 worker replica, 1 Kafka broker

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is not yet configured (template only). No gates to validate. Proceeding with industry best practices:

- Smallest viable diff: Adding event publishing to existing task routes (minimal code changes), new worker service, Kafka + Dapr infrastructure manifests. No refactoring of existing functionality.
- No secrets in code: All sensitive values in k8s Secrets or `.env` files (gitignored). Dapr component YAML references services by DNS name only.
- No unnecessary complexity: Direct HTTP calls to Dapr sidecar (no SDK). Plain KRaft YAML (no Helm, no operator). Single Kafka broker for dev.

## Project Structure

### Documentation (this feature)

```text
specs/003-kafka-dapr-cloud/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings (10 decisions)
├── data-model.md        # New entities + event schemas
├── quickstart.md        # Setup and deployment guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (new and modified files)

```text
hackathon-2/
├── backend/
│   ├── app/
│   │   ├── main.py                  # MODIFIED — import events router
│   │   ├── events/                  # NEW — event publishing module
│   │   │   ├── __init__.py
│   │   │   ├── publisher.py         # Dapr pub/sub publisher (HTTP to localhost:3500)
│   │   │   └── schemas.py           # Event payload dataclasses
│   │   ├── routes/
│   │   │   └── tasks.py             # MODIFIED — add event publishing after CRUD operations
│   │   └── chat_tools.py            # MODIFIED — add event publishing after tool executions
│   ├── requirements.txt             # MODIFIED — add httpx
│   └── Dockerfile                   # NO CHANGE
│
├── worker/                          # NEW — notification/analytics microservice
│   ├── Dockerfile                   # Multi-stage Python build (same pattern as backend)
│   ├── .dockerignore
│   ├── requirements.txt             # fastapi, uvicorn, httpx, sqlmodel, psycopg2-binary
│   └── app/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app + Dapr subscribe endpoint + health check
│       ├── events.py                # Event handlers: task.created/updated/completed/deleted
│       ├── notifications.py         # Overdue detection, daily summary generation
│       ├── analytics.py             # Completion rate, trends, time-to-complete aggregation
│       ├── models.py                # Notification, AnalyticsBucket, ProcessedEvent tables
│       ├── db.py                    # Neon PostgreSQL connection (same pattern as backend)
│       └── scheduler.py             # Background thread: overdue check (5min), daily summary
│
├── dapr/                            # NEW — Dapr component definitions
│   └── components/
│       ├── pubsub.yaml              # Kafka pub/sub component
│       └── statestore.yaml          # (Optional) PostgreSQL state store
│
├── compose.yaml                     # MODIFIED — add kafka, worker, dapr sidecars, zipkin
│
├── k8s/                             # MODIFIED — add new manifests
│   ├── namespace.yaml               # NO CHANGE
│   ├── configmap.yaml               # MODIFIED — add worker config vars
│   ├── secrets-template.yaml        # NO CHANGE
│   ├── backend-deployment.yaml      # MODIFIED — add Dapr annotations
│   ├── frontend-deployment.yaml     # NO CHANGE (no sidecar needed)
│   ├── ingress.yaml                 # MODIFIED — add /api/worker path
│   ├── hpa.yaml                     # NO CHANGE
│   ├── worker-deployment.yaml       # NEW — worker Deployment + Service
│   ├── kafka/                       # NEW — Kafka infrastructure
│   │   ├── kafka-statefulset.yaml   # Single-broker KRaft StatefulSet + Services
│   │   └── kafka-configmap.yaml     # server.properties ConfigMap
│   └── dapr/                        # NEW — Dapr components for k8s
│       ├── pubsub.yaml              # pubsub.kafka component
│       ├── tracing.yaml             # Zipkin tracing configuration
│       └── subscription.yaml        # (Optional) declarative subscription
│
└── frontend/                        # MINIMAL CHANGES
    └── (no changes for Phase 5 — notifications/analytics are API-only)
```

**Structure Decision**: Worker service follows the same pattern as the existing backend (Python/FastAPI with multi-stage Dockerfile). Dapr component YAML lives in both `dapr/components/` (for Docker Compose) and `k8s/dapr/` (for Kubernetes). Kafka manifests in `k8s/kafka/` subdirectory.

## Complexity Tracking

No constitution violations to justify — all additions follow established patterns (new microservice, infrastructure manifests).

---

## Phase 0: Research (Complete)

See [research.md](./research.md) for full findings. Key decisions:

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Kafka deployment | Plain KRaft YAML (single broker) | Lightest footprint, no Helm/operator, matches k8s/ pattern |
| 2 | Dapr installation | `dapr init -k` CLI | Single command, installs all components |
| 3 | Pub/sub component | `pubsub.kafka` | Dapr-native Kafka integration |
| 4 | Event schema | CloudEvents 1.0 (Dapr native) | Automatic envelope, no custom code |
| 5 | Tracing backend | Zipkin | Built into Dapr, 128-256MB RAM |
| 6 | Python ↔ Dapr | Direct HTTP to localhost:3500 | Zero new dependencies, full transparency |
| 7 | Worker architecture | Separate FastAPI microservice | Independent deployment, same tech stack |
| 8 | Analytics approach | Event-driven accumulation → PostgreSQL | Incremental updates, sub-100ms queries |
| 9 | Local dev | Docker Compose + Kafka + Dapr sidecars | Consistent with Phase IV pattern |
| 10 | Delivery guarantee | Dapr consumer groups + idempotent processing | At-least-once + dedup table |

---

## Phase 1: Design

### 1.1 Event Publishing Module (Backend)

**New module**: `backend/app/events/`

**publisher.py** — Publishes events to Dapr pub/sub:
- `publish_event(event_type: str, data: dict, user_id: str, task_id: int) -> None`
- Makes async HTTP POST to `http://localhost:3500/v1.0/publish/taskflow-pubsub/task-events`
- Fires-and-forgets (non-blocking) — if publish fails, logs warning but does not fail the request
- Stores event in `task_events` table for debugging/replay
- Uses `uuid4()` for event ID

**schemas.py** — Pydantic models for event payloads:
- `TaskCreatedPayload`, `TaskUpdatedPayload`, `TaskCompletedPayload`, `TaskDeletedPayload`
- Each includes `task_id`, `user_id`, and event-specific fields

### 1.2 Task Route Modifications (Backend)

**`backend/app/routes/tasks.py`** — Add event publishing after each CRUD operation:
- `create_task()` → publish `task.created` after `session.commit()`
- `update_task()` → publish `task.updated` with changed fields
- `toggle_complete()` → publish `task.completed` with completion time
- `delete_task()` → publish `task.deleted` with deleted task data

**`backend/app/chat_tools.py`** — Add event publishing after tool executions:
- Same events as task routes — the chatbot's `create_task`, `complete_task`, `delete_task`, `update_task` tools also need to publish events

### 1.3 Worker Service Design

**`worker/app/main.py`** — FastAPI application:
- `/dapr/subscribe` GET endpoint — returns subscription declaration
- `/events/task` POST endpoint — receives CloudEvents from Dapr
- `/health` GET endpoint — health check (checks DB connection + Dapr sidecar)
- `/api/notifications/{user_id}` GET — list user's notifications
- `/api/notifications/{user_id}/{notification_id}/read` PATCH — mark as read
- `/api/analytics/{user_id}` GET — return analytics summary for time window

**`worker/app/events.py`** — Event handler dispatch:
- Routes incoming CloudEvents by `type` field to specific handlers
- Checks `ProcessedEvent` table for idempotency before processing
- Handlers: `handle_task_created`, `handle_task_completed`, `handle_task_updated`, `handle_task_deleted`

**`worker/app/notifications.py`** — Notification generation:
- `check_overdue_tasks(session)` — queries tasks table, generates overdue alerts
- `generate_daily_summary(user_id, session)` — aggregates today's activity into summary notification

**`worker/app/analytics.py`** — Analytics aggregation:
- `update_analytics_bucket(event_type, data, session)` — increments per-user, per-day counters
- `get_analytics_summary(user_id, days, session)` — returns aggregated stats for time window

**`worker/app/scheduler.py`** — Background periodic tasks:
- Overdue check: every 5 minutes via `asyncio` loop
- Daily summary: once per day (configurable hour, default 23:00 UTC)

### 1.4 Kafka Infrastructure (Kubernetes)

**Single-broker KRaft deployment**:
- `k8s/kafka/kafka-configmap.yaml` — `server.properties` for KRaft mode
- `k8s/kafka/kafka-statefulset.yaml` — StatefulSet (1 replica) + headless Service + client Service
- Resources: 512MB request / 1GB limit, 250m / 500m CPU
- Storage: `emptyDir` (ephemeral for dev)
- Port: 9092 (PLAINTEXT)

### 1.5 Dapr Components (Kubernetes)

**`k8s/dapr/pubsub.yaml`** — Kafka pub/sub component:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-pubsub
  namespace: taskflow
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "kafka-svc.taskflow.svc.cluster.local:9092"
    - name: consumerGroup
      value: "taskflow-workers"
    - name: authType
      value: "none"
    - name: initialOffset
      value: "oldest"
```

**`k8s/dapr/tracing.yaml`** — Zipkin tracing configuration:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: taskflow-tracing
  namespace: taskflow
spec:
  tracing:
    samplingRate: "1"
    zipkin:
      endpointAddress: "http://zipkin.dapr-system.svc.cluster.local:9411/api/v2/spans"
```

### 1.6 Docker Compose Design (Local Dev)

Add to existing `compose.yaml`:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| kafka | apache/kafka:3.9.0 | 9092 | Message broker |
| worker | taskflow-worker:latest | 8001 | Notification/analytics service |
| backend-dapr | daprio/daprd:1.14.4 | — | Backend sidecar (network_mode: service:backend) |
| worker-dapr | daprio/daprd:1.14.4 | — | Worker sidecar (network_mode: service:worker) |
| zipkin | openzipkin/zipkin:latest | 9411 | Tracing dashboard |

Dapr sidecars use `network_mode: "service:<app>"` to share the network namespace with their app containers, making `localhost:3500` work naturally.

### 1.7 Ingress Modification

Add worker routes to `k8s/ingress.yaml`:
- `/api/worker` Prefix → `taskflow-worker:8001`

### 1.8 Deployment Annotations

Add Dapr annotations to `k8s/backend-deployment.yaml`:
```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "taskflow-backend"
  dapr.io/app-port: "8000"
  dapr.io/config: "taskflow-tracing"
```

Add Dapr annotations to `k8s/worker-deployment.yaml`:
```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "taskflow-worker"
  dapr.io/app-port: "8001"
  dapr.io/config: "taskflow-tracing"
```

Frontend does NOT get a Dapr sidecar (no event publishing or consuming needed).

---

## Implementation Order

| Phase | What | Files | Depends On |
|-------|------|-------|------------|
| 1 | Worker service scaffold (Dockerfile, main.py, db.py, models.py) | `worker/**` | Nothing |
| 2 | Event publisher module | `backend/app/events/**` | Nothing |
| 3 | Add event publishing to task routes | `backend/app/routes/tasks.py` | Phase 2 |
| 4 | Add event publishing to chat tools | `backend/app/chat_tools.py` | Phase 2 |
| 5 | Worker event handlers | `worker/app/events.py` | Phase 1 |
| 6 | Worker notification logic | `worker/app/notifications.py`, `worker/app/scheduler.py` | Phase 5 |
| 7 | Worker analytics logic | `worker/app/analytics.py` | Phase 5 |
| 8 | Worker API endpoints (notifications + analytics) | `worker/app/main.py` | Phase 6, 7 |
| 9 | Dapr component YAML (Docker Compose) | `dapr/components/**` | Nothing |
| 10 | Update compose.yaml (Kafka, worker, sidecars, Zipkin) | `compose.yaml` | Phase 1, 9 |
| 11 | **VALIDATE**: `docker compose up --build` and test full event flow | — | Phase 10 |
| 12 | Kafka k8s manifests | `k8s/kafka/**` | Nothing |
| 13 | Dapr k8s components + tracing config | `k8s/dapr/**` | Phase 12 |
| 14 | Worker k8s deployment | `k8s/worker-deployment.yaml` | Phase 1 |
| 15 | Modify backend deployment (Dapr annotations) | `k8s/backend-deployment.yaml` | Phase 13 |
| 16 | Update configmap + ingress for worker | `k8s/configmap.yaml`, `k8s/ingress.yaml` | Phase 14 |
| 17 | Add httpx to backend requirements | `backend/requirements.txt` | Phase 2 |
| 18 | **VALIDATE**: `kubectl apply -f k8s/` on Minikube, test full flow | — | Phase 12-16 |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Kafka + Dapr sidecars exceed Minikube memory | Pods crash, OOM | Increase Minikube to 6GB RAM; document in quickstart |
| Dapr sidecar injection race condition | App starts before sidecar is ready | Add startup probe or retry loop in publisher |
| Event publishing latency spikes | Perceived slowdown of task CRUD | Fire-and-forget pattern; never block on publish |
| Worker falls behind on events | Stale notifications/analytics | Monitor consumer lag; Kafka retains events for 24h |
| Shared PostgreSQL connection limits | Multiple services exhaust pool | Set pool_size=5 on worker (lighter than backend) |
| CloudEvents schema evolution | Old events incompatible with new worker | Use `datacontenttype` versioning; worker handles unknown fields gracefully |

---

## Follow-ups (Out of Scope)

- Email/push notification delivery (currently API-only)
- WebSocket real-time notification push to frontend
- Frontend UI for notifications and analytics dashboards
- Production Kafka cluster (multi-broker, replication)
- Helm chart packaging for Kafka and Dapr components
- CI/CD pipeline for worker image builds
- Dapr state store for chat session caching
