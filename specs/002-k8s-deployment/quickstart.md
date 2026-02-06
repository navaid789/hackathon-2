# Quickstart: Kubernetes Deployment

**Feature**: `002-k8s-deployment`
**Date**: 2026-02-04

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose V2)
- Minikube (`brew install minikube` / `choco install minikube` / `apt install minikube`)
- kubectl (`brew install kubectl` / bundled with Docker Desktop)
- Valid `.env` files with database URL, JWT secret, and API keys

## Local Development with Docker Compose

### 1. Start the application

```bash
# From repo root
docker compose up --build
```

### 2. Access the application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Stop the application

```bash
docker compose down
```

## Kubernetes Deployment (Minikube)

### 1. Start Minikube and enable addons

```bash
minikube start
minikube addons enable ingress
minikube addons enable metrics-server
```

### 2. Build images in Minikube's Docker daemon

```bash
eval $(minikube docker-env)
docker build -t taskflow-backend:latest ./backend
docker build -t taskflow-frontend:latest --build-arg NEXT_PUBLIC_API_URL=http://taskflow.local ./frontend
```

### 3. Create secrets

```bash
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic taskflow-secrets \
  --namespace taskflow \
  --from-literal=DATABASE_URL='your-neon-db-url' \
  --from-literal=JWT_SECRET='your-jwt-secret' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --from-literal=GROQ_API_KEY='your-groq-key' \
  --from-literal=BETTER_AUTH_SECRET='your-auth-secret'
```

### 4. Apply manifests

```bash
kubectl apply -f k8s/
```

### 5. Add hosts entry

```bash
echo "$(minikube ip) taskflow.local" | sudo tee -a /etc/hosts
```

### 6. Access the application

- Application: http://taskflow.local

### 7. Verify deployment

```bash
# Check all pods are running
kubectl get pods -n taskflow

# Check services
kubectl get svc -n taskflow

# Check ingress
kubectl get ingress -n taskflow

# Check HPA status
kubectl get hpa -n taskflow
```

### 8. Teardown

```bash
kubectl delete -f k8s/
minikube stop
```

## Troubleshooting

| Issue | Command | What to check |
|-------|---------|---------------|
| Pods not starting | `kubectl describe pod <name>` | Image pull errors, env var issues |
| Ingress not routing | `kubectl describe ingress` | Host/path rules, backend service names |
| HPA showing `<unknown>` | `kubectl get hpa` | Metrics-server addon enabled? |
| DB connection failures | `kubectl logs <backend-pod>` | DATABASE_URL correct in secret? |
| Frontend API errors | Browser DevTools Network tab | NEXT_PUBLIC_API_URL matches ingress host? |
