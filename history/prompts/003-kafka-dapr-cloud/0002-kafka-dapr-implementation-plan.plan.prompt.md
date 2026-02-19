---
id: "0002"
title: "Kafka Dapr Implementation Plan"
stage: plan
date: 2026-02-06
surface: agent
model: claude-opus-4-5-20251101
feature: 003-kafka-dapr-cloud
branch: 003-kafka-dapr-cloud
user: nm
command: /sp.plan
labels: ["kafka", "dapr", "event-driven", "architecture", "implementation-plan"]
links:
  spec: specs/003-kafka-dapr-cloud/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-kafka-dapr-cloud/plan.md
  - specs/003-kafka-dapr-cloud/research.md
  - specs/003-kafka-dapr-cloud/data-model.md
  - specs/003-kafka-dapr-cloud/quickstart.md
  - CLAUDE.md
tests:
  - All 10 research decisions resolved with rationale
  - Plan implementation order validated (18 phases with dependencies)
---

## Prompt

/sp.plan

(Generate technical architecture and implementation plan for Phase 5: Advanced cloud deployment with Kafka and Dapr, based on spec at specs/003-kafka-dapr-cloud/spec.md)

## Response snapshot

Generated complete implementation plan with 4 design artifacts:

**research.md** — 10 technical decisions:
1. Kafka: Plain KRaft YAML (single broker, no Helm/operator)
2. Dapr: `dapr init -k` CLI installation
3. Pub/Sub: `pubsub.kafka` Dapr component
4. Events: CloudEvents 1.0 (Dapr native)
5. Tracing: Zipkin (built into Dapr)
6. Python to Dapr: Direct HTTP to localhost:3500 (no SDK)
7. Worker: Separate FastAPI microservice
8. Analytics: Event-driven accumulation to PostgreSQL
9. Local dev: Docker Compose + Kafka + Dapr sidecars
10. Delivery: Dapr consumer groups + idempotent processing

**data-model.md** — 4 new entities: TaskEvent, Notification, AnalyticsBucket, ProcessedEvent + CloudEvents schema for 4 event types

**quickstart.md** — Setup guide for both Docker Compose and Minikube deployment

**plan.md** — 18-phase implementation order covering: worker scaffold, event publisher, task route modifications, worker event handlers, notifications, analytics, Dapr components, Docker Compose, Kafka k8s, worker k8s deployment, Dapr annotations

Agent context (CLAUDE.md) updated with new technologies.

## Outcome

- Impact: Complete technical architecture for event-driven microservices with Kafka + Dapr
- Tests: All 10 research decisions documented with alternatives and rationale
- Files: 5 files created/modified (plan.md, research.md, data-model.md, quickstart.md, CLAUDE.md)
- Next prompts: /sp.tasks to generate actionable task breakdown from the plan
- Reflection: Chose simplest viable options throughout — plain KRaft YAML over Strimzi, direct HTTP over Dapr SDK, Zipkin over Jaeger — to minimize complexity for a hackathon project while preserving upgrade paths

## Evaluation notes (flywheel)

- Failure modes observed: Background research agents were lost during context continuation; consolidated research inline instead
- Graders run and results (PASS/FAIL): All NEEDS CLARIFICATION resolved — PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
