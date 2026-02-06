# Quickstart: Kafka + Dapr Cloud Deployment

**Branch**: `003-kafka-dapr-cloud` | **Date**: 2026-02-06

## Prerequisites

- Docker Desktop / Docker Engine with Docker Compose V2
- Minikube 1.30+ with `kubectl`
- Dapr CLI 1.14+ (`brew install dapr/tap/dapr-cli` or see [dapr.io](https://docs.dapr.io/getting-started/install-dapr-cli/))
- Node.js 20+, Python 3.12+ (for local development outside containers)
- Existing `.env` files from Phase IV (backend/.env, frontend/.env.local)

---

## Option A: Docker Compose (Local Development)

### 1. Start all services

```bash
docker compose up --build -d
```

This starts: backend, frontend, worker, kafka, backend-dapr, worker-dapr, zipkin.

### 2. Verify services are running

```bash
docker compose ps
```

Expected: All 7 services running.

### 3. Verify Kafka is ready

```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

Should return (auto-created on first publish):
```
task-events
```

### 4. Verify Dapr sidecars

```bash
# Backend sidecar health
curl http://localhost:3500/v1.0/healthz

# Worker sidecar health
curl http://localhost:3501/v1.0/healthz
```

### 5. Verify Zipkin tracing

Open: http://localhost:9411

### 6. Test the flow

```bash
# Create a task via the API (requires auth token)
# Or use the UI at http://localhost:3000

# Check worker logs for event consumption
docker compose logs worker -f
```

### 7. Check notifications API

```bash
curl http://localhost:8001/api/notifications/{user_id}
```

### 8. Check analytics API

```bash
curl http://localhost:8001/api/analytics/{user_id}?days=7
```

### 9. Stop all services

```bash
docker compose down
```

---

## Option B: Kubernetes (Minikube)

### 1. Start Minikube (if not running)

```bash
minikube start --memory=6144 --cpus=4
```

> Note: 6GB RAM recommended — Kafka + Dapr + existing services need more memory than Phase IV.

### 2. Install Dapr on the cluster

```bash
dapr init -k --wait
```

Verify:
```bash
dapr status -k
```

All components should show `Running`.

### 3. Enable metrics-server (for HPA)

```bash
minikube addons enable metrics-server
```

### 4. Apply namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 5. Create secrets

```bash
kubectl create secret generic taskflow-secrets -n taskflow \
  --from-literal=DATABASE_URL="your-neon-connection-string" \
  --from-literal=JWT_SECRET="your-jwt-secret" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=BETTER_AUTH_SECRET="your-auth-secret"
```

### 6. Deploy Kafka

```bash
kubectl apply -f k8s/kafka/ -n taskflow
```

Wait for Kafka pod to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=kafka -n taskflow --timeout=120s
```

### 7. Deploy Dapr components

```bash
kubectl apply -f k8s/dapr/ -n taskflow
```

### 8. Deploy application services

```bash
kubectl apply -f k8s/configmap.yaml -n taskflow
kubectl apply -f k8s/backend-deployment.yaml -n taskflow
kubectl apply -f k8s/frontend-deployment.yaml -n taskflow
kubectl apply -f k8s/worker-deployment.yaml -n taskflow
```

### 9. Deploy Ingress and HPA

```bash
minikube addons enable ingress
kubectl apply -f k8s/ingress.yaml -n taskflow
kubectl apply -f k8s/hpa.yaml -n taskflow
```

### 10. Configure /etc/hosts

```bash
echo "$(minikube ip) taskflow.local" | sudo tee -a /etc/hosts
```

### 11. Verify deployment

```bash
# All pods running
kubectl get pods -n taskflow

# Dapr sidecars injected (each app pod should have 2/2 containers)
kubectl get pods -n taskflow -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Check Zipkin
kubectl port-forward svc/zipkin -n dapr-system 9411:9411 &
open http://localhost:9411
```

### 12. Test

Open: http://taskflow.local

Create tasks, complete them, and verify:
- Worker logs show event consumption: `kubectl logs -l app=taskflow-worker -n taskflow -f`
- Notifications appear: `curl http://taskflow.local/api/worker/notifications/{user_id}`
- Analytics work: `curl http://taskflow.local/api/worker/analytics/{user_id}?days=7`

---

## Distributed Tracing with Zipkin

### Docker Compose Access

Zipkin UI: http://localhost:9411

### Kubernetes Access

```bash
# Port-forward Zipkin service
kubectl port-forward svc/zipkin -n taskflow 9411:9411

# Open in browser
open http://localhost:9411
```

### Verifying End-to-End Traces

1. **Create a task** via UI (http://localhost:3000) or API
2. **Open Zipkin** (http://localhost:9411)
3. **Search for traces**:
   - Service: `backend` or `worker`
   - Click "Run Query"
4. **Expected trace flow**:
   ```
   backend → taskflow-pubsub (Kafka) → worker
   ```

### Trace Components

| Service | App ID | Description |
|---------|--------|-------------|
| Backend | `backend` | Task CRUD operations, event publishing |
| Worker | `worker` | Event consumption, notifications, analytics |
| Kafka | `taskflow-pubsub` | Message broker (visible in traces) |

### Sampling Rate

Default: 100% (`samplingRate: "1"` in tracing config)

To reduce for production:
```yaml
spec:
  tracing:
    samplingRate: "0.1"  # 10% sampling
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Kafka pod CrashLoopBackOff | Insufficient memory | Increase Minikube memory: `minikube start --memory=6144` |
| Dapr sidecar not injected | Missing annotation | Verify `dapr.io/enabled: "true"` in deployment spec |
| Events not published | Dapr sidecar not ready | Check `daprd` container logs: `kubectl logs <pod> -c daprd -n taskflow` |
| Worker not receiving events | Component misconfigured | Verify `taskflow-pubsub` component: `kubectl get component -n taskflow` |
| Traces not appearing in Zipkin | Tracing config not applied | Verify `taskflow-tracing` config: `kubectl get configuration -n taskflow` |
| Connection refused on localhost:3500 | Sidecar not running | In Docker Compose, ensure `network_mode: "service:backend"` on dapr sidecar |
