# Phase 0 Research: Kafka + Dapr Cloud Deployment

**Branch**: `003-kafka-dapr-cloud` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)

## Research Summary

10 technical decisions researched across 4 domains: Kafka deployment, Dapr runtime, event patterns, and worker architecture.

---

## Decision 1: Kafka Deployment on Minikube

### Options Considered

| Option | Install Complexity | RAM Footprint | KRaft Support | External Dependencies |
|--------|-------------------|---------------|---------------|----------------------|
| Strimzi Operator | Medium | ~1-1.5GB | Yes (default since 0.39) | Operator CRDs |
| Bitnami Helm Chart | Low | ~512MB-1GB | Yes (default) | Helm |
| Confluent Platform (CFK) | High | ~4-8GB | Yes | Helm + License |
| **Plain KRaft YAML** | **Low** | **~512-768MB** | **Native** | **None** |

### Decision: Plain KRaft YAML manifests (single broker)

### Rationale
- Matches existing `k8s/` directory pattern (all plain YAML, no Helm — spec says "Helm chart packaging" is out of scope)
- Smallest footprint: 512-768MB RAM, 250-500m CPU for a single broker
- Kafka 3.9+ supports KRaft natively (no ZooKeeper needed) — `process.roles=broker,controller`
- Dapr abstracts Kafka interaction entirely — app never touches Kafka APIs directly
- Full transparency: ~100-120 lines of YAML across 3-4 files, every line readable
- Migration path: can upgrade to Strimzi later by swapping StatefulSet for a Kafka CR

### Key Configuration
- Image: `apache/kafka:3.9.0`
- KRaft mode: `process.roles=broker,controller`, `node.id=1`
- Listeners: `PLAINTEXT://:9092` (broker), `CONTROLLER://:9093`
- Single partition, 24h retention, auto-create topics enabled
- Storage: `emptyDir` for dev (ephemeral, acceptable for hackathon)

---

## Decision 2: Dapr Installation Method

### Options Considered

| Option | Ease | Components Installed | Cluster Impact |
|--------|------|---------------------|----------------|
| **`dapr init -k`** | **Simplest** | **Dapr operator, sidecar injector, placement, sentry** | **Standard** |
| Helm chart | Medium | Same + more configurability | Configurable |
| Plain manifests | Hard | Manual per-component | Minimal |

### Decision: `dapr init -k` (Dapr CLI)

### Rationale
- Single command installs all Dapr control plane components on any k8s cluster
- Installs: `dapr-operator`, `dapr-sidecar-injector`, `dapr-placement`, `dapr-sentry` in `dapr-system` namespace
- Works immediately on Minikube with no additional configuration
- For Docker Compose local dev: `dapr init` installs local Dapr runtime + Redis + Zipkin
- Resource overhead per sidecar: ~30-50MB RAM, ~10-20m CPU (negligible)

### Sidecar Injection
Annotations on pod templates:
```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "taskflow-backend"
  dapr.io/app-port: "8000"
  dapr.io/log-level: "info"
```
Dapr sidecar injector automatically adds the `daprd` container to annotated pods.

---

## Decision 3: Dapr Pub/Sub Component for Kafka

### Decision: `pubsub.kafka` component type

### Component Definition
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
    - name: maxMessageBytes
      value: "1048576"
```

### Rationale
- Dapr natively supports Kafka pub/sub with automatic CloudEvents wrapping
- `consumerGroup` ensures at-least-once delivery with offset tracking
- `initialOffset: oldest` ensures worker catches up on restart
- App publishes via: `POST http://localhost:3500/v1.0/publish/taskflow-pubsub/task-events`
- App subscribes via: Dapr calls a POST endpoint on the app when events arrive

---

## Decision 4: Event Schema Format

### Decision: CloudEvents (Dapr native format)

### Rationale
- Dapr automatically wraps all pub/sub messages in CloudEvents 1.0 envelope
- No custom envelope code needed — Dapr handles `id`, `source`, `type`, `specversion`, `time`
- The app only provides the `data` payload and `type` field
- Schema versioning via `datacontenttype` and custom extension attributes

### Event Examples

**task.created**:
```json
{
  "specversion": "1.0",
  "type": "task.created",
  "source": "/taskflow/backend",
  "id": "evt-uuid-here",
  "time": "2026-02-06T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "title": "Buy groceries",
    "priority": "medium",
    "due_date": "2026-02-10T00:00:00Z",
    "created_at": "2026-02-06T10:30:00Z"
  }
}
```

**task.completed**:
```json
{
  "type": "task.completed",
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "completed": true,
    "completed_at": "2026-02-07T14:00:00Z",
    "time_to_complete_hours": 27.5
  }
}
```

**task.updated**:
```json
{
  "type": "task.updated",
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "changes": {
      "priority": {"old": "medium", "new": "high"},
      "title": {"old": "Buy groceries", "new": "Buy organic groceries"}
    }
  }
}
```

**task.deleted**:
```json
{
  "type": "task.deleted",
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "title": "Buy groceries",
    "deleted_at": "2026-02-08T09:00:00Z"
  }
}
```

---

## Decision 5: Distributed Tracing Backend

### Options Considered

| Option | RAM | Ease | UI | Dapr Integration |
|--------|-----|------|----|-----------------|
| **Zipkin** | **~128-256MB** | **Built into Dapr init** | **Good** | **Native** |
| Jaeger | ~512MB-1GB | Manual install | Better | Supported |
| OpenTelemetry Collector + backend | ~256MB+ | Complex | Depends | Supported |

### Decision: Zipkin

### Rationale
- Dapr `init -k` can install Zipkin automatically with `--enable-ha=false`
- Dapr's tracing configuration component points to Zipkin out of the box
- Lightweight: ~128-256MB RAM
- Adequate for dev/hackathon — simple UI for viewing traces
- W3C Trace Context headers propagated automatically by Dapr sidecars

### Tracing Component
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

---

## Decision 6: Python Integration with Dapr

### Options Considered

| Option | Dependency | Complexity | Flexibility |
|--------|-----------|------------|-------------|
| **Direct HTTP to localhost:3500** | **httpx (already common)** | **Low** | **High** |
| Dapr Python SDK (`dapr`) | New pip package | Medium | Medium |
| Dapr gRPC | New pip package + protobuf | High | High |

### Decision: Direct HTTP calls via `httpx`

### Rationale
- Zero new dependencies (httpx or even `requests`/`urllib3` already available; FastAPI includes `httpx` as test dependency)
- Dapr sidecar runs at `http://localhost:3500` — standard REST calls
- Publish: `POST http://localhost:3500/v1.0/publish/{pubsub-name}/{topic}`
- Invoke: `POST http://localhost:3500/v1.0/invoke/{app-id}/method/{method}`
- State: `GET/POST http://localhost:3500/v1.0/state/{store-name}/{key}`
- The Dapr Python SDK is a thin wrapper around these HTTP calls anyway
- Using raw HTTP keeps the code transparent and debuggable

### Subscribe Pattern
Dapr calls the app's endpoints when events arrive. The app registers subscriptions via:
```python
@router.get("/dapr/subscribe")
def subscribe():
    return [
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "task-events",
            "route": "/events/task"
        }
    ]

@router.post("/events/task")
def handle_task_event(event: dict):
    # Process the CloudEvents envelope
    event_type = event.get("type")
    data = event.get("data", {})
    # ... handle event
    return {"status": "SUCCESS"}
```

---

## Decision 7: Notification Worker Architecture

### Decision: Separate FastAPI microservice (same tech stack)

### Rationale
- Same Python/FastAPI stack as the main backend — shared knowledge, shared patterns
- Runs as an independent container with its own Dockerfile, deployment, and health check
- Dapr sidecar handles event subscription — worker registers `/dapr/subscribe` endpoint
- Two responsibilities: (1) consume events for notifications/analytics, (2) expose API for retrieving results

### Worker Structure
```
worker/
├── Dockerfile              # Same multi-stage as backend
├── requirements.txt        # fastapi, uvicorn, httpx, sqlmodel, psycopg2-binary
├── app/
│   ├── main.py             # FastAPI app + Dapr subscribe endpoint
│   ├── events.py           # Event handlers (task.created, task.completed, etc.)
│   ├── notifications.py    # Overdue detection, daily summary generation
│   ├── analytics.py        # Aggregation: completion rate, trends, time-to-complete
│   ├── models.py           # Notification, AnalyticsSummary SQLModel tables
│   ├── db.py               # Same Neon PostgreSQL connection (shared DB)
│   └── scheduler.py        # Background thread for periodic tasks (overdue check, daily summary)
└── .dockerignore
```

### Scheduled Tasks
- Use a simple background thread with `asyncio` scheduler (not Dapr cron binding — avoids extra component complexity)
- Overdue check: every 5 minutes
- Daily summary: once per day at configurable time
- Both write results to `notifications` table in PostgreSQL

---

## Decision 8: Analytics Data Approach

### Options Considered

| Option | Complexity | Latency | Storage |
|--------|-----------|---------|---------|
| Event replay on query | Low code | High latency | No extra storage |
| **In-memory accumulation + DB persist** | **Medium** | **Low latency** | **Small** |
| Materialized views in PostgreSQL | Medium | Low latency | Medium |

### Decision: Event-driven accumulation persisted to PostgreSQL

### Rationale
- Worker consumes events and incrementally updates analytics aggregates in a `task_analytics` table
- On `task.created`: increment `total_created`, record daily bucket
- On `task.completed`: increment `total_completed`, compute `time_to_complete`, update daily bucket
- Analytics API reads pre-computed aggregates — sub-100ms response time
- Uses same Neon PostgreSQL as the rest of the application (no new infrastructure)
- Data is per-user, per-day granularity — very small storage footprint

---

## Decision 9: Docker Compose Local Development

### Decision: Add Kafka + Dapr sidecar containers to existing compose.yaml

### Approach
- Add `kafka` service: `apache/kafka:3.9.0` with KRaft env vars
- Add `dapr-placement` service: `daprio/placement` for local Dapr
- Add Dapr sidecar containers as separate services (one per app): `daprio/daprd`
- Each sidecar is configured via CLI flags and component YAML mounted as volumes
- Component YAML files stored in `dapr/components/` directory

### compose.yaml additions
```yaml
services:
  kafka:
    image: apache/kafka:3.9.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 24
    ports:
      - "9092:9092"

  backend-dapr:
    image: daprio/daprd:1.14.4
    command: ["./daprd",
      "--app-id", "taskflow-backend",
      "--app-port", "8000",
      "--dapr-http-port", "3500",
      "--resources-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:backend"
    depends_on:
      - backend
      - kafka

  worker-dapr:
    image: daprio/daprd:1.14.4
    command: ["./daprd",
      "--app-id", "taskflow-worker",
      "--app-port", "8001",
      "--dapr-http-port", "3500",
      "--resources-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:worker"
    depends_on:
      - worker
      - kafka
```

---

## Decision 10: Kafka Consumer Groups and Delivery Guarantees

### Decision: Dapr-managed consumer groups with at-least-once delivery

### Rationale
- Dapr's Kafka pub/sub manages consumer group offsets automatically
- `consumerGroup: "taskflow-workers"` in component config
- `initialOffset: "oldest"` ensures worker processes all unread events after restart
- Dapr commits offsets after the app returns HTTP 200 from the subscription handler
- If the handler returns non-200 or the worker crashes, the event is redelivered (at-least-once)
- Worker must handle idempotency: use event ID as dedup key in the notifications/analytics tables
- Events for a single user are ordered because Kafka preserves order within a partition; the Dapr component can use `partitionKey` (set to user_id) to ensure per-user ordering

### Idempotency Strategy
- Store processed event IDs in a `processed_events` table (event_id TEXT PRIMARY KEY)
- Before processing, check if event_id exists; if yes, skip
- This ensures exactly-once semantics from the application perspective

---

## Consolidated Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Message Broker | Apache Kafka (KRaft) | 3.9.0 | Event streaming |
| Runtime | Dapr | 1.14.x | Sidecar for pub/sub, invocation, tracing |
| Tracing | Zipkin | latest | Distributed trace visualization |
| Event Format | CloudEvents 1.0 | — | Standard event envelope (Dapr native) |
| Worker Framework | FastAPI + Uvicorn | 0.115.0 / 0.30.0 | Notification/analytics microservice |
| Python HTTP | httpx | latest | Dapr sidecar communication |
| Database | Neon PostgreSQL | — | Shared DB for notifications + analytics |
| Kafka Image | apache/kafka | 3.9.0 | KRaft single-broker |
| Dapr Sidecar | daprio/daprd | 1.14.4 | Per-service sidecar container |
