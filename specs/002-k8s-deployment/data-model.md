# Data Model: Kubernetes Deployment

**Feature**: `002-k8s-deployment`
**Date**: 2026-02-04

## Overview

This feature introduces no new application-level data entities. The existing data model (Task, ChatSession, ChatMessage, User) remains unchanged. The "entities" in this feature are infrastructure resources — Kubernetes objects that describe the desired deployment state.

## Infrastructure Entities

### Container Image

| Attribute | Description |
|-----------|-------------|
| Registry | GHCR (`ghcr.io/<owner>`) |
| Name | `taskflow-backend`, `taskflow-frontend` |
| Tag | Git commit SHA short (7 chars) or `latest` |

**Relationships**: Referenced by Deployment manifests via `spec.containers[].image`.

### Deployment (Backend)

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-backend` |
| Replicas | 2 (min), 5 (max via HPA) |
| Image | `ghcr.io/<owner>/taskflow-backend:<tag>` |
| Port | 8000 |
| Resources (request) | CPU: 100m, Memory: 128Mi |
| Resources (limit) | CPU: 500m, Memory: 256Mi |
| Strategy | RollingUpdate (maxSurge: 1, maxUnavailable: 0) |
| Env from Secret | `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, `GROQ_API_KEY` |
| Env from ConfigMap | `AI_PROVIDER` |

### Deployment (Frontend)

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-frontend` |
| Replicas | 1 |
| Image | `ghcr.io/<owner>/taskflow-frontend:<tag>` |
| Port | 3000 |
| Resources (request) | CPU: 100m, Memory: 128Mi |
| Resources (limit) | CPU: 250m, Memory: 256Mi |
| Strategy | RollingUpdate (maxSurge: 1, maxUnavailable: 0) |

### Service (Backend)

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-backend` |
| Type | ClusterIP |
| Port | 8000 → 8000 |
| Selector | `app: taskflow-backend` |

### Service (Frontend)

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-frontend` |
| Type | ClusterIP |
| Port | 80 → 3000 |
| Selector | `app: taskflow-frontend` |

### Ingress

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-ingress` |
| Host | `taskflow.local` |
| Rule 1 | `/api(/|$)(.*)` → `taskflow-backend:8000` |
| Rule 2 | `/` → `taskflow-frontend:80` |
| Annotations | `nginx.ingress.kubernetes.io/rewrite-target: /$2` (for `/api` prefix stripping) |

### Secret

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-secrets` |
| Keys | `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, `GROQ_API_KEY` |

**Note**: A template file (`k8s/secrets-template.yaml`) will be committed with placeholder values. Actual secrets are applied manually and never committed.

### ConfigMap

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-config` |
| Keys | `AI_PROVIDER` (default: `openai`) |

### HPA (Backend)

| Attribute | Value |
|-----------|-------|
| Name | `taskflow-backend-hpa` |
| Target | Deployment `taskflow-backend` |
| Min replicas | 2 |
| Max replicas | 5 |
| Metric | CPU utilization |
| Target value | 70% |

## Environment Variable Mapping

| Variable | Source | Used By | Sensitive |
|----------|--------|---------|-----------|
| `DATABASE_URL` | Secret | Backend, Frontend | Yes |
| `JWT_SECRET` | Secret | Backend | Yes |
| `OPENAI_API_KEY` | Secret | Backend | Yes |
| `GROQ_API_KEY` | Secret | Backend | Yes |
| `AI_PROVIDER` | ConfigMap | Backend | No |
| `NEXT_PUBLIC_API_URL` | Build ARG | Frontend (build time) | No |
| `BETTER_AUTH_SECRET` | Secret | Frontend | Yes |
| `BETTER_AUTH_URL` | ConfigMap | Frontend | No |

## No Schema Changes

The PostgreSQL schema is unchanged. No migrations are needed for this feature.
