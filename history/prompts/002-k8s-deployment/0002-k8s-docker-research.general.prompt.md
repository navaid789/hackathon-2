---
id: 0002
title: K8s Docker Deployment Research
stage: general
date: 2026-02-04
surface: agent
model: claude-opus-4-5-20251101
feature: 002-k8s-deployment
branch: main
user: nm
command: research
labels: ["kubernetes", "docker", "nextjs", "fastapi", "deployment", "research"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/002-k8s-deployment/0002-k8s-docker-research.general.prompt.md
tests:
  - none
---

## Prompt

Research the following topics for a Kubernetes deployment of a FastAPI + Next.js application with Neon PostgreSQL (external DB). The project uses:
- Backend: Python 3.12, FastAPI 0.115, uvicorn, psycopg2-binary, openai/groq SDKs
- Frontend: Next.js 16, React 19, better-auth, Tailwind CSS 4, pg driver
- Database: External Neon PostgreSQL (not in cluster)

Research these specific questions and provide concrete answers:

1. **Container Registry Choice**: Docker Hub vs GHCR vs other for a hackathon project. Which is simplest to set up?
2. **Next.js Standalone Output Mode**: How to configure Next.js 16 for standalone output in Docker. What config changes are needed in next.config.ts?
3. **Python Base Image**: Best base image for FastAPI in production (python:3.12-slim vs alpine). What's the size/compatibility tradeoff?
4. **Ingress Controller for Local K8s**: Best ingress controller for Minikube/Kind for development (nginx-ingress vs traefik).
5. **Readiness Probe Design**: Should the readiness probe check DB connectivity? What's the best practice for external DB readiness checks?
6. **Docker Compose vs Docker Compose V2**: Current best practice for local container orchestration file naming and syntax.
7. **Next.js Environment Variables in Docker**: How NEXT_PUBLIC_* vars work at build time vs runtime in containerized Next.js. Implications for the API URL.
8. **HPA with Metrics Server**: Does Minikube/Kind include metrics-server by default for HPA? What addon is needed?

## Response snapshot

Comprehensive research covering 8 deployment topics with concrete recommendations:
1. GHCR recommended for GitHub-hosted hackathon projects (simpler auth, free for public repos)
2. Single line `output: "standalone"` in next.config.ts + multi-stage Dockerfile with manual static/public copy
3. python:3.12-slim-bookworm recommended over Alpine (psycopg2-binary incompatible with musl, 10-50x slower builds)
4. Minikube NGINX addon (one command) for hackathon; note NGINX Ingress retiring March 2026
5. Do NOT check DB in readiness probe -- use two-tier health (shallow /readyz + deep /healthz/deep for monitoring only)
6. Use compose.yaml (not docker-compose.yml), no version: key, use `docker compose` command
7. NEXT_PUBLIC_* baked at build time -- use ARG/ENV for single-env, avoid NEXT_PUBLIC entirely for multi-env
8. Minikube: `minikube addons enable metrics-server` (not enabled by default); Kind: manual install + --kubelet-insecure-tls

## Outcome

- Impact: Research completed for all 8 deployment topics with actionable config snippets
- Tests: none
- Files: PHR only
- Next prompts: Create Dockerfiles, compose.yaml, K8s manifests based on research findings
- Reflection: Research confirms stack-specific gotchas (psycopg2+Alpine, NEXT_PUBLIC build-time baking, NGINX retirement)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A - research task
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Apply findings to create actual Docker and K8s configuration files
