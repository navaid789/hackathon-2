# Tasks: Kafka + Dapr Cloud Deployment

**Input**: Design documents from `/specs/003-kafka-dapr-cloud/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Exact file paths included in descriptions

## Path Conventions

- **Backend**: `backend/app/` (Python/FastAPI)
- **Worker**: `worker/app/` (Python/FastAPI - new microservice)
- **Infrastructure**: `k8s/`, `dapr/`, `compose.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create worker service scaffold and Dapr component definitions

- [ ] T001 [P] Create worker directory structure: `worker/`, `worker/app/`, `worker/app/__init__.py`
- [ ] T002 [P] Create worker requirements.txt with fastapi, uvicorn, httpx, sqlmodel, psycopg2-binary in `worker/requirements.txt`
- [ ] T003 [P] Create worker Dockerfile (multi-stage build, same pattern as backend) in `worker/Dockerfile`
- [ ] T004 [P] Create worker .dockerignore in `worker/.dockerignore`
- [ ] T005 [P] Create Dapr components directory: `dapr/components/`
- [ ] T006 [P] Add httpx to backend requirements in `backend/requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create worker database connection module (same pattern as backend) in `worker/app/db.py`
- [ ] T008 Create worker models: Notification, AnalyticsBucket, ProcessedEvent in `worker/app/models.py`
- [ ] T009 Create event publisher module __init__ in `backend/app/events/__init__.py`
- [ ] T010 Create event payload schemas (TaskCreatedPayload, etc.) in `backend/app/events/schemas.py`
- [ ] T011 Create Dapr pub/sub publisher (fire-and-forget HTTP to localhost:3500) in `backend/app/events/publisher.py`

**Checkpoint**: Foundation ready - event publishing and worker models exist

---

## Phase 3: User Story 1 - Event-Driven Task Activity Stream (Priority: P1) 🎯 MVP

**Goal**: Every task CRUD operation publishes an event to Kafka via Dapr

**Independent Test**: Create/update/complete/delete a task → verify events appear in Kafka topic; task CRUD still responds under 500ms

### Implementation for User Story 1

- [ ] T012 [US1] Add event publishing to create_task() in `backend/app/routes/tasks.py`
- [ ] T013 [US1] Add event publishing to update_task() with change tracking in `backend/app/routes/tasks.py`
- [ ] T014 [US1] Add event publishing to toggle_complete() with time-to-complete in `backend/app/routes/tasks.py`
- [ ] T015 [US1] Add event publishing to delete_task() with deleted data in `backend/app/routes/tasks.py`
- [ ] T016 [US1] Add event publishing to chat tool create_task in `backend/app/chat_tools.py`
- [ ] T017 [US1] Add event publishing to chat tool complete_task in `backend/app/chat_tools.py`
- [ ] T018 [US1] Add event publishing to chat tool delete_task in `backend/app/chat_tools.py`
- [ ] T019 [US1] Add event publishing to chat tool update_task in `backend/app/chat_tools.py`
- [ ] T020 [P] [US1] Create Kafka pub/sub component YAML (Docker Compose) in `dapr/components/pubsub.yaml`
- [ ] T021 [P] [US1] Create Kafka service in Docker Compose (apache/kafka:3.9.0 KRaft) in `compose.yaml`
- [ ] T022 [P] [US1] Add backend-dapr sidecar service (daprio/daprd:1.14.4) to `compose.yaml`

**Checkpoint**: Task events flow to Kafka via Dapr sidecar; primary CRUD operations unaffected

---

## Phase 4: User Story 2 - Task Notification Worker (Priority: P2)

**Goal**: Worker consumes events, generates overdue alerts and daily summaries

**Independent Test**: Create overdue tasks → worker generates alerts; trigger daily summary → verify content via API

### Implementation for User Story 2

- [ ] T023 [US2] Create worker FastAPI app with /health endpoint in `worker/app/main.py`
- [ ] T024 [US2] Add Dapr subscription endpoint (/dapr/subscribe) in `worker/app/main.py`
- [ ] T025 [US2] Add event receiver endpoint (/events/task) in `worker/app/main.py`
- [ ] T026 [US2] Create event handler dispatch with idempotency check in `worker/app/events.py`
- [ ] T027 [US2] Implement handle_task_created, handle_task_completed, handle_task_updated, handle_task_deleted in `worker/app/events.py`
- [ ] T028 [US2] Create notification generation logic (check_overdue_tasks) in `worker/app/notifications.py`
- [ ] T029 [US2] Create daily summary generation logic in `worker/app/notifications.py`
- [ ] T030 [US2] Create background scheduler (5min overdue check, daily summary) in `worker/app/scheduler.py`
- [ ] T031 [US2] Add GET /api/notifications/{user_id} endpoint in `worker/app/main.py`
- [ ] T032 [US2] Add PATCH /api/notifications/{user_id}/{notification_id}/read endpoint in `worker/app/main.py`
- [ ] T033 [P] [US2] Add worker service to Docker Compose in `compose.yaml`
- [ ] T034 [P] [US2] Add worker-dapr sidecar service to Docker Compose in `compose.yaml`
- [ ] T035 [P] [US2] Add Zipkin service to Docker Compose in `compose.yaml`

**Checkpoint**: Worker consumes events, stores notifications, exposes API

---

## Phase 5: User Story 3 - Service Communication via Runtime Abstraction (Priority: P3)

**Goal**: All pub/sub goes through Dapr sidecars; infrastructure is swappable via config

**Independent Test**: Deploy with Dapr sidecars → verify task CRUD + chatbot work identically; change component config without code changes

### Implementation for User Story 3

- [ ] T036 [P] [US3] Create Kafka ConfigMap (server.properties for KRaft) in `k8s/kafka/kafka-configmap.yaml`
- [ ] T037 [P] [US3] Create Kafka StatefulSet + Services in `k8s/kafka/kafka-statefulset.yaml`
- [ ] T038 [P] [US3] Create Dapr pub/sub component for k8s in `k8s/dapr/pubsub.yaml`
- [ ] T039 [P] [US3] Create Dapr tracing configuration for k8s in `k8s/dapr/tracing.yaml`
- [ ] T040 [US3] Add Dapr annotations to backend deployment in `k8s/backend-deployment.yaml`
- [ ] T041 [US3] Create worker Deployment + Service with Dapr annotations in `k8s/worker-deployment.yaml`
- [ ] T042 [US3] Update ConfigMap with worker-related vars in `k8s/configmap.yaml`
- [ ] T043 [US3] Add /api/worker route to Ingress in `k8s/ingress.yaml`

**Checkpoint**: All services communicate via Dapr sidecars on k8s; Kafka is infrastructure-only

---

## Phase 6: User Story 4 - Task Productivity Analytics (Priority: P4)

**Goal**: Analytics API returns completion rate, avg time-to-complete, daily trends

**Independent Test**: Complete tasks over days → query analytics endpoint → verify stats are correct

### Implementation for User Story 4

- [ ] T044 [US4] Create analytics bucket update logic (increment counters on events) in `worker/app/analytics.py`
- [ ] T045 [US4] Create get_analytics_summary function (query buckets, compute stats) in `worker/app/analytics.py`
- [ ] T046 [US4] Call update_analytics_bucket from event handlers in `worker/app/events.py`
- [ ] T047 [US4] Add GET /api/analytics/{user_id} endpoint with days param in `worker/app/main.py`

**Checkpoint**: Analytics endpoint returns accurate productivity stats

---

## Phase 7: User Story 5 - Distributed Observability (Priority: P5)

**Goal**: End-to-end tracing visible in Zipkin dashboard

**Independent Test**: Create task → view trace in Zipkin showing backend → Kafka → worker path

### Implementation for User Story 5

- [ ] T048 [US5] Ensure Dapr tracing config applied to all services (verify taskflow-tracing in annotations)
- [ ] T049 [US5] Document Zipkin access (port-forward or Ingress) in `specs/003-kafka-dapr-cloud/quickstart.md`
- [ ] T050 [US5] Verify trace propagation by testing full flow: task create → event → worker

**Checkpoint**: Traces visible end-to-end in Zipkin

---

## Phase 8: Polish & Validation

**Purpose**: Final validation and cleanup

- [ ] T051 Run `docker compose up --build` and validate full event flow locally
- [ ] T052 Test: Create task → verify event in Kafka → verify worker logs consumption
- [ ] T053 Test: Create overdue task → verify notification generated
- [ ] T054 Test: Complete tasks → verify analytics endpoint returns correct stats
- [ ] T055 Run `kubectl apply -f k8s/` on Minikube and validate full flow
- [ ] T056 Test: Zipkin dashboard shows distributed traces
- [ ] T057 Verify worker health check at /health reports Dapr + DB status
- [ ] T058 Update quickstart.md with troubleshooting notes if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational - MVP, must complete first
- **US2 (Phase 4)**: Depends on US1 (needs events to consume) + Foundational
- **US3 (Phase 5)**: Depends on Foundational - infrastructure only, can parallel with US2
- **US4 (Phase 6)**: Depends on US2 (needs event handlers in worker)
- **US5 (Phase 7)**: Depends on US3 (needs Dapr tracing config)
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

```
Foundational (T007-T011)
    │
    ├──► US1: Event Publishing (T012-T022) ──► US2: Notification Worker (T023-T035)
    │                                               │
    │                                               └──► US4: Analytics (T044-T047)
    │
    └──► US3: Dapr/Kafka Infra (T036-T043) ──► US5: Observability (T048-T050)
```

### Parallel Opportunities

**Phase 1 (all parallel)**:
- T001, T002, T003, T004, T005, T006 can all run simultaneously

**Phase 2 (sequential)**:
- T007 → T008 (models need db)
- T009 → T010 → T011 (schemas before publisher)

**Phase 3 (US1)**:
- T012-T019 (task routes + chat tools) are sequential (same files)
- T020, T021, T022 can run in parallel (different files)

**Phase 4 (US2)**:
- T033, T034, T035 can run in parallel (compose.yaml additions)

**Phase 5 (US3)**:
- T036, T037, T038, T039 can all run in parallel (different k8s files)

---

## Parallel Execution Examples

### Launch all setup tasks:
```bash
# All can run simultaneously (different files)
Task: T001 "Create worker directory structure"
Task: T002 "Create worker requirements.txt"
Task: T003 "Create worker Dockerfile"
Task: T004 "Create worker .dockerignore"
Task: T005 "Create Dapr components directory"
Task: T006 "Add httpx to backend requirements"
```

### Launch all k8s infrastructure tasks (US3):
```bash
# All can run simultaneously (different files)
Task: T036 "Create Kafka ConfigMap"
Task: T037 "Create Kafka StatefulSet + Services"
Task: T038 "Create Dapr pub/sub component"
Task: T039 "Create Dapr tracing configuration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T011)
3. Complete Phase 3: US1 - Event Publishing (T012-T022)
4. **STOP and VALIDATE**: `docker compose up --build`, create tasks, verify events in Kafka
5. Demo: Events flowing through Dapr to Kafka

### Full Feature Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Events publishing → **Demo MVP**
3. US2 → Worker consuming + notifications → **Demo notifications**
4. US3 → Kubernetes manifests → **Demo k8s deployment**
5. US4 → Analytics API → **Demo productivity stats**
6. US5 → Tracing → **Demo observability**
7. Polish → Final validation

---

## Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| 1: Setup | T001-T006 | 6/6 | Worker scaffold, Dapr components |
| 2: Foundational | T007-T011 | 0/5 | DB, models, event publisher |
| 3: US1 (P1) | T012-T022 | 3/11 | Event publishing + Docker Compose Kafka |
| 4: US2 (P2) | T023-T035 | 3/13 | Notification worker |
| 5: US3 (P3) | T036-T043 | 4/8 | Kubernetes Kafka + Dapr infra |
| 6: US4 (P4) | T044-T047 | 0/4 | Analytics aggregation |
| 7: US5 (P5) | T048-T050 | 0/3 | Distributed tracing |
| 8: Polish | T051-T058 | 0/8 | Validation |
| **Total** | **58** | **16** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- US1 is MVP — demo after completing Phase 3
