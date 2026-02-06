# Feature Specification: Advanced Cloud Deployment with Kafka and Dapr

**Feature Branch**: `003-kafka-dapr-cloud`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "Advanced cloud deployment with Kafka and Dapr for event-driven microservices architecture"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Event-Driven Task Activity Stream (Priority: P1)

As a TaskFlow user, I want all my task actions (create, update, complete, delete) to produce events that are processed asynchronously, so that the system can react to my activity without slowing down my workflow — enabling features like notifications, analytics, and audit trails.

**Why this priority**: This is the foundational capability that everything else in Phase 5 depends on. Without events flowing through a message broker, no downstream consumers (notifications, analytics, activity feed) can exist. It transforms the application from a synchronous request-response model to an event-driven architecture.

**Independent Test**: Can be fully tested by performing task CRUD operations and verifying that corresponding events appear in the message broker topic. The main application continues to respond within normal latency, proving events are published asynchronously.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they create a new task via the UI or chatbot, **Then** a `task.created` event is published to the message broker within 2 seconds containing the task details and user ID.
2. **Given** a logged-in user, **When** they mark a task as complete, **Then** a `task.completed` event is published containing the task ID, completion timestamp, and time-to-complete duration.
3. **Given** a logged-in user, **When** they update a task's title, priority, or due date, **Then** a `task.updated` event is published containing the changed fields and their previous values.
4. **Given** a logged-in user, **When** they delete a task, **Then** a `task.deleted` event is published containing the deleted task's data for audit purposes.
5. **Given** the message broker is temporarily unavailable, **When** a user performs a task action, **Then** the primary operation (database write) still succeeds and the event is queued for retry.
6. **Given** events are being published, **When** a platform operator inspects the event stream, **Then** each event follows a standard envelope format with event type, timestamp, user ID, and payload.

---

### User Story 2 - Task Notification Worker (Priority: P2)

As a TaskFlow user, I want to receive proactive notifications about my tasks — such as overdue alerts and daily task summaries — so that I stay on top of my responsibilities without having to manually check the app.

**Why this priority**: Notifications are the most user-visible outcome of the event-driven architecture. They demonstrate immediate value by proactively alerting users about overdue tasks and providing daily productivity summaries. This requires a new background worker service that consumes events independently from the main application.

**Independent Test**: Can be tested by creating tasks with past due dates and verifying the notification worker detects and logs overdue alerts. A daily summary can be triggered manually and verified for accuracy against the user's task list.

**Acceptance Scenarios**:

1. **Given** a user has tasks with due dates in the past, **When** the notification worker runs its overdue check, **Then** an overdue alert is generated for each task that is past due and not completed.
2. **Given** the notification worker is running, **When** it consumes a `task.completed` event, **Then** it logs the completion for the user's daily summary.
3. **Given** it is the end of the day, **When** the daily summary is generated, **Then** it includes: tasks completed today, tasks still pending, and tasks overdue — and the summary is accessible via an API endpoint.
4. **Given** the notification worker crashes and restarts, **When** it reconnects to the message broker, **Then** it resumes processing from where it left off without missing or duplicating events.

---

### User Story 3 - Service Communication via Runtime Abstraction (Priority: P3)

As a platform operator, I want all inter-service communication to go through a distributed application runtime (sidecar pattern), so that I can swap messaging infrastructure, add observability, and manage service discovery without modifying application code.

**Why this priority**: This decouples application logic from infrastructure concerns. Once services communicate through the runtime abstraction, changing the message broker, adding encryption, or switching state stores requires only configuration changes — not code changes. This is a strategic investment in operational flexibility.

**Independent Test**: Can be tested by deploying all services with runtime sidecars on the existing cluster, verifying that existing functionality (task CRUD, chatbot, auth) continues to work, and then confirming that service-to-service calls route through the sidecar proxy.

**Acceptance Scenarios**:

1. **Given** the backend and frontend are deployed with runtime sidecars, **When** a user performs normal task operations, **Then** all functionality works identically to the non-sidecar deployment.
2. **Given** a service needs to publish an event, **When** it calls the sidecar's publish endpoint, **Then** the event is delivered to the configured message broker without the service knowing the broker's address or protocol.
3. **Given** a service needs to invoke another service, **When** it calls the sidecar's invocation endpoint, **Then** the request is routed to the target service with built-in retries, timeouts, and circuit breaking.
4. **Given** a platform operator wants to switch message brokers, **When** they update the runtime component configuration, **Then** the applications continue working without any code changes or redeployment.

---

### User Story 4 - Task Productivity Analytics (Priority: P4)

As a TaskFlow user, I want to view analytics about my task management patterns — including completion rates, average time-to-complete, and daily/weekly trends — so that I can understand and improve my productivity.

**Why this priority**: Analytics provide long-term value by giving users insight into their habits. This depends on US1 (event stream) and US2 (worker) being in place to aggregate event data. It adds a new dimension to the product beyond simple task CRUD.

**Independent Test**: Can be tested by creating and completing multiple tasks over several days, then querying the analytics endpoint to verify that completion rates, averages, and trends are calculated correctly.

**Acceptance Scenarios**:

1. **Given** a user has completed tasks over the past 7 days, **When** they request their analytics, **Then** they see: total tasks created, total completed, completion rate percentage, and average time-to-complete.
2. **Given** a user has task activity spanning multiple days, **When** they view daily trends, **Then** they see a per-day breakdown of tasks created vs. tasks completed for the last 7 days.
3. **Given** a user has no task activity, **When** they request analytics, **Then** they see a meaningful empty state (e.g., "No activity yet. Create your first task to start tracking productivity.").

---

### User Story 5 - Distributed Observability (Priority: P5)

As a platform operator, I want end-to-end distributed tracing across all services (backend, frontend, notification worker), so that I can diagnose latency issues, trace event flows, and monitor system health in the multi-service architecture.

**Why this priority**: Observability is essential for operating a distributed system, but it is lower priority than the core event-driven features because the system can function without it. Once the multi-service architecture is in place, tracing becomes critical for production debugging.

**Independent Test**: Can be tested by performing a task operation that triggers an event, then verifying the trace appears in the tracing dashboard showing the full path: user request → backend → event publish → worker consumption.

**Acceptance Scenarios**:

1. **Given** tracing is enabled across all services, **When** a user creates a task, **Then** a single trace ID connects the request from the backend through event publication to worker consumption.
2. **Given** the tracing dashboard is accessible, **When** an operator queries by trace ID, **Then** they see all spans with timing information, service names, and any errors.
3. **Given** a service is experiencing high latency, **When** the operator views traces, **Then** they can identify which service or step is the bottleneck.

---

### Edge Cases

- What happens when the message broker is down during a task operation? The primary operation (database write) must still succeed; events should be retried or queued locally.
- What happens when the notification worker falls behind on processing events? Events should not be lost; the worker should catch up from its last committed offset.
- What happens when a user performs many rapid task operations (e.g., bulk complete)? Events should be published individually but the UI should not block waiting for event confirmation.
- How does the system handle event schema evolution? Older events in the stream must still be consumable by newer worker versions (backward compatibility).
- What happens when the runtime sidecar is not running? The application should fail fast with a clear error rather than hanging indefinitely.
- What happens when two services publish conflicting events for the same task? Event ordering within a single task must be preserved (partition by task ID or user ID).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST publish an event to the message broker for every task state change (create, update, complete, delete).
- **FR-002**: Each event MUST contain a standard envelope with: event type, event ID, timestamp, user ID, and payload data.
- **FR-003**: Event publishing MUST NOT block or delay the primary task operation (database write). If publishing fails, the task operation MUST still succeed.
- **FR-004**: System MUST include a notification worker service that runs independently from the main backend and consumes task events from the message broker.
- **FR-005**: The notification worker MUST detect overdue tasks and generate overdue alerts accessible via an API endpoint.
- **FR-006**: The notification worker MUST generate a daily task summary per user containing: tasks created, tasks completed, tasks overdue, and tasks pending.
- **FR-007**: The notification worker MUST resume processing from its last committed position after a restart, without missing or duplicating events.
- **FR-008**: All inter-service communication (event publishing, service invocation) MUST go through a distributed application runtime sidecar, not directly to infrastructure endpoints.
- **FR-009**: The runtime configuration MUST be declarative and changeable without modifying application code.
- **FR-010**: System MUST provide a task analytics API endpoint that returns: total tasks created, total completed, completion rate, average time-to-complete, and daily trends for a configurable time window (default: 7 days).
- **FR-011**: The analytics data MUST be derived from the event stream, not by querying the primary task database synchronously.
- **FR-012**: System MUST support distributed tracing with a single trace ID propagated across all service boundaries (backend → message broker → worker).
- **FR-013**: A tracing dashboard MUST be accessible to platform operators showing traces, spans, and service dependency maps.
- **FR-014**: Each service (backend, frontend, notification worker) MUST have its own container image, deployment manifest, and health check.
- **FR-015**: The message broker MUST be deployed as part of the cluster infrastructure with its own manifests.
- **FR-016**: System MUST handle event schema versioning so that older events remain consumable by newer worker versions.
- **FR-017**: Events for a single user's tasks MUST be processed in order (no out-of-order delivery within a user's partition).
- **FR-018**: The notification worker MUST expose a health check endpoint that reports whether it is connected to the message broker and actively consuming events.

### Key Entities

- **Task Event**: A record of a task state change, containing event type (created/updated/completed/deleted), event ID, timestamp, user ID, task ID, and a payload with the task data and changed fields. Events are immutable once published.
- **Notification**: A generated alert or summary for a user, containing notification type (overdue_alert/daily_summary), target user ID, content, generation timestamp, and read/unread status.
- **Analytics Summary**: An aggregation of a user's task activity over a time window, containing user ID, time window, total created, total completed, completion rate, average time-to-complete, and daily breakdown.
- **Runtime Component**: A declarative configuration for a sidecar capability (pub/sub, state store, service invocation), containing component name, type, and connection metadata. Changed by operators, not by application code.
- **Trace**: A distributed request path across services, containing trace ID, spans (one per service hop), timing data, and status. Used for operational debugging.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every task state change (create, update, complete, delete) produces a corresponding event within 2 seconds, with 99.9% reliability during normal operation.
- **SC-002**: Task operations (create, update, complete, delete) maintain their current response time (under 500ms) even with event publishing enabled — event publishing does not add perceptible latency.
- **SC-003**: The notification worker processes events within 5 seconds of publication under normal load.
- **SC-004**: Overdue task alerts are generated within 1 minute of a task becoming overdue.
- **SC-005**: Daily task summaries are accurate to within the last 5 minutes of activity at generation time.
- **SC-006**: The analytics endpoint returns results for a 7-day window in under 1 second.
- **SC-007**: After a worker restart, no events are missed or duplicated (at-least-once delivery with idempotent processing).
- **SC-008**: Switching the message broker configuration requires zero application code changes and zero application redeployments.
- **SC-009**: A distributed trace is visible end-to-end (backend → broker → worker) for every task operation within the tracing dashboard.

## Assumptions

- The existing Kubernetes cluster from Phase IV is operational and accessible.
- The external Neon PostgreSQL database continues to serve as the primary data store; the event stream supplements but does not replace it.
- The notification worker will initially log notifications to its own API endpoint; email/push notification delivery channels are out of scope for this phase.
- Analytics data is derived from events and may have slight eventual-consistency lag (acceptable for productivity insights).
- The project uses Apache Kafka as the message broker and Dapr as the distributed application runtime, as specified in the project roadmap.
- Local development will use Docker Compose with Kafka and Dapr containers; Kubernetes deployment uses manifests with Dapr annotations and Strimzi/Kafka operator.

## Out of Scope

- Email, SMS, or push notification delivery (notifications are API-accessible only).
- Real-time WebSocket push of notifications to the frontend.
- Multi-tenant analytics or cross-user aggregations.
- CI/CD pipeline automation.
- TLS/HTTPS termination on Ingress.
- Helm chart packaging.
- Production-grade Kafka cluster sizing (single-broker is acceptable for this phase).

## Dependencies

- Phase IV (Kubernetes deployment) must be complete and operational.
- Docker Compose and Kubernetes cluster (Minikube) from Phase IV.
- Dapr runtime must be installable on the target Kubernetes cluster.
- Kafka (or Kafka-compatible broker) must be deployable on the cluster.
