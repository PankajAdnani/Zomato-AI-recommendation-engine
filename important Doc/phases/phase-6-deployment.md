# Phase 6 — Deployment & Production Architecture

> Status: **Documented & Operational**  
> Parent: [architecture.md](../architecture.md)  
> Depends on: [Phase 5](phase-5-output-display.md)

---

## 🎯 Objectives

Define, standardize, and operationalize the deployment strategy for the decoupled **Next.js Frontend** and **FastAPI Backend** architecture, enabling reproducible local staging, containerized deployments, and cloud production environments with zero downtime.

---

## 🏗️ Deployment Topologies

The system supports two enterprise deployment topologies:

### Topology 1: Fully Containerized Monorepo / Microservices (Docker Compose / AWS ECS / GCP Cloud Run)

Both services run as isolated, containerized microservices within a private virtual network. An API gateway or reverse proxy handles routing and SSL/TLS termination.

```mermaid
flowchart TD
    Client["Client Browser / Mobile Web"] -->|HTTPS :443| LB["Load Balancer / Reverse Proxy (Nginx / Cloudflare)"]
    
    subgraph Container_Network ["Private Virtual Network (Docker Bridge / VPC)"]
        LB -->|Port 3000| NextFrontend["Next.js 16 Frontend Container (Node.js 20/24)"]
        NextFrontend -->|Internal Rewrite /api/*| FastAPIServer["FastAPI Backend Container (Python 3.10+ / Uvicorn)"]
        LB -.->|Direct API calls /api/* (Optional)| FastAPIServer
        
        FastAPIServer -->|Local Parquet Read| ParquetStore[("Embedded Dataset Store\ndata/processed/restaurants.parquet")]
    end
    
    FastAPIServer -->|HTTPS REST API / gRPC| GeminiAPI["Google Gemini LLM Cloud (gemini-3.5-flash-lite)"]
```

### Topology 2: Decoupled Edge + Serverless Backend (Vercel + Cloud Run / Railway)

- **Frontend**: Deployed to **Vercel** or **Cloudflare Pages** at the edge for global CDN distribution, automatic asset optimization, and microsecond TTFB.
- **Backend**: Deployed to **GCP Cloud Run**, **AWS App Runner**, or **Railway/Render** as an auto-scaling container.
- **Edge Rewrites**: Vercel `vercel.json` or Next.js `next.config.ts` rewrites proxy `/api/:path*` to the backend origin, avoiding CORS preflight latency.

---

## 🐳 Containerization Strategy

### 1. Backend Container (`Dockerfile.backend`)
- **Base**: `python:3.11-slim` (minimal attack surface, ~150MB footprint).
- **Security**: Runs under a non-root unprivileged service user (`appuser:10001`).
- **Dependencies**: Wheels cached using pip cache mounts.
- **Dataset Storage**: `data/processed/restaurants.parquet` is bundled directly into the read-only layer (or mounted via an external volume/S3 bucket for dynamic updates).
- **Healthcheck**: Built-in curl/Python probe targeting `/api/health`.

### 2. Frontend Container (`frontend/Dockerfile`)
- **Base**: `node:20-alpine` (multi-stage build).
  - Stage 1 (`deps`): Installs production packages.
  - Stage 2 (`builder`): Compiles Next.js standalone server with Turbopack.
  - Stage 3 (`runner`): Minimal runtime container utilizing Next.js `output: 'standalone'` mode (< 100MB).
- **Environment**: Configured with `NEXT_PUBLIC_API_URL` or internal rewrite targets.

### 3. Unified Orchestration (`docker-compose.yml`)
- Spins up both frontend and backend in one command:
  ```bash
  docker compose up --build
  ```
- Exposes:
  - Frontend: `http://localhost:3000`
  - Backend API: `http://localhost:8000`

---

## 🔐 Environment Variables & Secrets Management

| Variable Name | Required | Default | Description |
|---------------|:--------:|---------|-------------|
| `GEMINI_API_KEY` | **Yes** | *None* | Google Gemini API key for `gemini-3.5-flash-lite` inference. |
| `GEMINI_MODEL` | No | `gemini-3.5-flash-lite` | Gemini model tag (kept on free-tier standard). |
| `FASTAPI_HOST` | No | `0.0.0.0` | Binding interface for Uvicorn ASGI server. |
| `FASTAPI_PORT` | No | `8000` | Port for the backend API. |
| `NEXT_PUBLIC_API_URL` | No | `""` (proxied via `/api`) | Public backend endpoint if decoupled from Next rewrites. |
| `CORS_ORIGINS` | No | `["*"]` | Allowed CORS origins for cross-domain API access. |

> **Security Rule**: API keys are injected at container runtime via secret managers (AWS Secrets Manager, GCP Secret Manager, or GitHub Secrets) and never baked into container images or checked into Git.

---

## 🩺 Health Checks & Observability

### Endpoint: `GET /api/health`

Returns instantaneous operational status:
```json
{
  "status": "ok",
  "service": "Zomato Recommendation Engine",
  "restaurants_count": 9249,
  "localities_count": 92,
  "llm_model": "gemini-3.5-flash-lite"
}
```

### Logging & Metrics
- **Structured JSON Logging**: Request latency, filter latency (`filter_ms`), LLM inference latency (`llm_ms`), candidate count, and status codes.
- **Fail-Safe Fallbacks**: If Gemini API limits or quota timeouts occur, the server gracefully reverts to deterministic heuristic ranking without terminating user sessions.

---

## 🔄 CI/CD Automation Pipeline

Continuous Integration & Deployment via GitHub Actions (`.github/workflows/deploy.yml`):

1. **Lint & Test**:
   - Python unit tests (`pytest tests/`) validating preference parsing, candidate filtering, anti-hallucination checks, and FastAPI endpoints (24/24 tests).
   - Next.js type check & build (`npm run build`).
2. **Container Image Build & Push**:
   - Multi-arch Docker images built and tagged with commit SHA.
   - Pushed to container registry (GitHub Container Registry `ghcr.io` or AWS ECR).
3. **Deployment Trigger**:
   - Automated rolling update to Cloud Run / ECS / Railway.

---

## 📋 Change Log

| Date | Change |
|------|--------|
| 2026-11-18 | Phase 6 drafted & added to architecture documentation covering containerization, Next.js/FastAPI decoupled topologies, Docker Compose, and secrets management. |
