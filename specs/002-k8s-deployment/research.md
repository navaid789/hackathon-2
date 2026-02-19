# Research: Kubernetes Deployment

**Feature**: `002-k8s-deployment`
**Date**: 2026-02-04

## R1: Container Registry

**Decision**: Use GHCR (GitHub Container Registry) for image hosting. For local development with Minikube, use `minikube docker-env` to build images directly into Minikube's Docker daemon, eliminating the need for a registry during development.

**Rationale**: GHCR integrates natively with the GitHub repository (free for public repos, 500MB free for private). No separate account or credentials needed beyond the existing GitHub access. For local k8s testing, `eval $(minikube docker-env)` lets you build and use images without pushing anywhere.

**Alternatives considered**:
- Docker Hub: requires separate account, rate limits on free tier (100 pulls/6hr)
- Self-hosted: unnecessary complexity for a hackathon

## R2: Next.js Standalone Output Mode

**Decision**: Set `output: "standalone"` in `next.config.ts`. This produces a self-contained build with only the necessary dependencies copied, resulting in a ~150-200MB image instead of ~890MB.

**Rationale**: Standalone mode bundles the minimal Node.js server and only required `node_modules`. This is the official Docker deployment strategy recommended by Next.js.

**Config change required**:
```typescript
const nextConfig: NextConfig = {
  output: "standalone",
};
```

**Dockerfile pattern**: Copy `.next/standalone`, `.next/static`, and `public/` into the runtime image. Entry point is `node server.js`.

## R3: Python Base Image

**Decision**: Use `python:3.12-slim-bookworm` as the base image for the backend.

**Rationale**: The `slim` variant is ~120MB (vs ~920MB for full). Alpine (`python:3.12-alpine`) would be smaller (~50MB) but `psycopg2-binary` relies on glibc and fails on Alpine's musl libc — it would require building `psycopg2` from source with `libpq-dev`, adding complexity and build time.

**Alternatives considered**:
- `python:3.12-alpine`: Incompatible with `psycopg2-binary` without extra build steps
- `python:3.12` (full): ~920MB, wastes space with unnecessary tools

## R4: Ingress Controller

**Decision**: Use NGINX Ingress Controller via `minikube addons enable ingress` for local development.

**Rationale**: Single command setup, well-documented, sufficient for hackathon scope. NGINX Ingress is the most common controller and most tutorials/examples use it.

**Alternatives considered**:
- Traefik: Auto-discovery is nice but more complex to configure for simple path-based routing
- Gateway API: Future standard but more verbose for simple use cases

**Note**: NGINX Ingress Controller is being retired March 2026. For production beyond this hackathon, consider Traefik or Gateway API.

## R5: Readiness Probe Design

**Decision**: Use a shallow readiness check at `/health` (existing endpoint). Do NOT check database connectivity in the readiness probe.

**Rationale**: If the readiness probe checks the external Neon PostgreSQL, a transient DB hiccup would mark all pods as not-ready simultaneously, causing a full outage even though the pods themselves are healthy. The liveness probe uses the same `/health` endpoint. The backend already has `pool_pre_ping=True` which handles stale DB connections at the application level.

**Alternatives considered**:
- Separate `/readyz` endpoint with DB check: Risk of cascading failure outweighs benefit
- Startup probe with DB check: Adds complexity; the backend already handles DB unavailability gracefully via SQLModel error handling

## R6: Local Container Orchestration

**Decision**: Use `compose.yaml` (canonical filename) with Docker Compose V2 (`docker compose` command, no hyphen).

**Rationale**: Docker Compose V1 (`docker-compose` with hyphen) is deprecated. The canonical filename is `compose.yaml` per the Docker Compose Specification.

## R7: Next.js Environment Variables in Docker

**Decision**: Pass `NEXT_PUBLIC_API_URL` as a build argument (`ARG`) in the Dockerfile. For k8s, rebuild the image with the correct API URL or use a single known URL (the Ingress hostname).

**Rationale**: `NEXT_PUBLIC_*` variables are inlined into the JavaScript bundle at `next build` time. They cannot be changed at runtime without rebuilding. For this project, the API URL is known at build time:
- Local Docker: `http://localhost:8000`
- Kubernetes: The Ingress hostname (e.g., `http://taskflow.local`)

**Implications**: The same frontend image cannot be reused across environments with different API URLs without rebuilding. This is acceptable for a hackathon — for production, a runtime injection pattern would be needed.

## R8: HPA and Metrics Server

**Decision**: Enable metrics-server addon in Minikube: `minikube addons enable metrics-server`.

**Rationale**: Metrics-server is NOT enabled by default in Minikube. HPA requires it to read CPU/memory utilization. Without it, HPA stays in `<unknown>` state and never scales.

**For Kind**: Install metrics-server via Helm chart or kubectl manifest. Kind does not have addon support.
