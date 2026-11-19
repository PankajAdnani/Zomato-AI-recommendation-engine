# Architecture: AI-Powered Restaurant Recommendation System (Zomato Use Case)

## Overview

AI-powered restaurant recommendation service inspired by Zomato. Combines structured restaurant data from the Hugging Face Zomato dataset with Google Gemini LLM reasoning (`gemini-3.5-flash-lite`) for personalized, grounded recommendations based on location, budget, cuisine, rating, and free-text mood preferences.

**Problem statement:** [Problem statement.md](Problem%20statement.md)

---

### High-Level Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      Client Web Browser / Mobile                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS (Port 3000 / 443)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Frontend Layer: Next.js 16 (React 19)                  │
│   • Zomato Brand Theme (Navbar, Hero, Circular Dishes, Feature Cards)  │
│   • Multi-Criteria Preference Controls (Location, Budget, Cuisine)     │
│   • Active Debounced Live Search (Sub-millisecond query across 9,249+) │
│   • Performance Metrics Dashboard & AI Recommendation Cards View       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Internal Proxy / Rewrites (/api/*)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Backend API Layer: FastAPI (Uvicorn)                 │
│   • /api/health    • /api/metadata    • /api/search    • /api/trending │
│   • /api/recommend (POST with Preference Validation & Orchestration)   │
└───────────┬────────────────────────────────────────────────┬───────────┘
            │                                                │
            ▼                                                ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     Structured Filtering      │        │      Google Gemini LLM        │
│   • Multi-criteria filter     │        │   • Model: gemini-3.5-flash-  │
│   • Heuristic score ranking   │        │     lite (standard tier)      │
│   • Progressive relaxation    │        │   • Grounded prompt context   │
│   • Candidate extraction      │        │   • Anti-hallucination check  │
└───────────┬───────────────────┘        │   • Heuristic fallback logic  │
            │                            └───────────────▲───────────────┘
            ▼                                            │
┌───────────────────────────────┐                        │
│   Embedded Parquet Storage    │                        │
│   • data/processed/           │────────────────────────┘
│     restaurants.parquet       │   Context Candidates
│   • 9,249 verified records    │
└───────────────────────────────┘
```

### Production Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| **Frontend** | Next.js 16 + React 19 + TypeScript | High-performance SSR/Client web app with authentic Zomato design system |
| **Styling** | Tailwind CSS + Zomato Custom Styles | Responsive layout, animations, badges, and card grids |
| **Backend API** | FastAPI + Uvicorn (Python 3.10+) | High-throughput asynchronous REST API server |
| **Data Layer** | Pandas, PyArrow, Parquet | 9,249 deduplicated restaurants offline columnar cache |
| **Filtering Engine** | NumPy, Scikit-learn heuristics | Multi-tier progressive constraint relaxation and scoring |
| **AI / LLM Engine** | Google Gemini (`gemini-3.5-flash-lite`) | Contextual reasoning, personalized explanations, highlights |
| **Deployment** | Docker, Docker Compose, Vercel/Cloud Run | Containerized microservices with reverse proxying |

---

## Phase Documents (edit independently)

Each phase lives in its own file so implementation details can change without rewriting the whole architecture.

| Phase | Document | Status |
|-------|----------|--------|
| 0 | [phase-0-foundation.md](phases/phase-0-foundation.md) | **Implemented** |
| 1 | [phase-1-data-ingestion.md](phases/phase-1-data-ingestion.md) | **Implemented** |
| 2 | [phase-2-user-input.md](phases/phase-2-user-input.md) | **Implemented** |
| 3 | [phase-3-filtering.md](phases/phase-3-filtering.md) | **Implemented** |
| 4 | [phase-4-llm-engine.md](phases/phase-4-llm-engine.md) | **Implemented** |
| 5 | [phase-5-output-display.md](phases/phase-5-output-display.md) | **Implemented** |
| 6 | [phase-6-deployment.md](phases/phase-6-deployment.md) | **Implemented & Operational** |

---

## End-to-End Sequence

```text
1. User interacts with Next.js Frontend (Browse, Search, or Input Preferences)
2. Search Bar executes debounced client-side queries against GET /api/search
3. User submits Recommendation form (Location, Budget, Cuisine, Min Rating, Mood)
4. Next.js proxies POST /api/recommend to FastAPI backend
5. FastAPI validates payload via Pydantic UserPreferences
6. Candidate Filtering Engine scores and extracts Top-K candidates from Parquet cache
7. If 0 strict matches: Progressive Relaxation expands budget/rating constraints
8. Grounded prompt constructed with Candidate Context + Schema Constraints
9. Google Gemini API (gemini-3.5-flash-lite) generates personalized recommendations
10. Anti-hallucination layer validates candidate IDs against candidate pool
11. FastAPI returns formatted RecommendationCards + latency performance metrics
12. Next.js renders interactive results view with Metrics Dashboard & Zomato cards
```

---

## 🚢 Deployment Architecture

The system is architected for clean separation of concerns, containerization, and horizontal scalability across cloud platforms.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     Edge / Ingress Layer                               │
│        (Cloudflare / AWS CloudFront / Nginx / Vercel Edge)             │
│        • SSL/TLS Termination (:443)                                    │
│        • Global CDN Caching & Edge Optimization                        │
│        • DDoS Protection & Rate Limiting                               │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
    Routes to Frontend (:3000)                       │ Proxies /api/* (:8000)
                    ▼                                ▼
┌────────────────────────────────────────┐ ┌─────────────────────────────┐
│       Next.js Frontend Container       │ │  FastAPI Backend Container  │
│       • Node.js 20/24 Alpine           │ │  • Python 3.11-slim         │
│       • Standalone output mode         │ │  • Uvicorn ASGI Server      │
│       • Responsive SSR & Client Hydr.  │ │  • 4x Worker concurrency    │
└────────────────────────────────────────┘ └──────────────┬──────────────┘
                                                          │
                                         ┌────────────────┴──────────────┐
                                         │  Read-Only Data Volume Mount  │
                                         │  • restaurants.parquet        │
                                         └───────────────────────────────┘
```

### 1. Deployment Topologies

#### Topology A: Unified Containerized Deployment (Docker Compose / AWS ECS / Cloud Run)
- Both services are packaged into Docker images:
  - `Dockerfile.backend`: Light Python 3.11 image (~150MB) running Uvicorn.
  - `frontend/Dockerfile`: Multi-stage Next.js standalone container (~90MB).
- Managed via `docker-compose.yml`:
  ```bash
  docker compose up --build -d
  ```
- Suitable for single-instance staging, self-hosted VPS, or managed container clouds (AWS ECS, GCP Cloud Run, Azure Container Apps, DigitalOcean App Platform, Render).

#### Topology B: Decoupled Edge & Serverless Deployment (Vercel + Cloud Run / Railway)
- **Frontend**: Deployed directly on **Vercel** with native Next.js Turbopack compilation and edge routing.
- **Backend**: Deployed on **GCP Cloud Run**, **Railway**, or **Render** with autoscaling (0 to N instances).
- **Zero-CORS Proxying**: Next.js `next.config.ts` rewrites seamlessly route `/api/:path*` to the backend URL.

### 2. Environment Configuration & Secrets Management

| Variable | Scope | Purpose |
|----------|-------|---------|
| `GEMINI_API_KEY` | Backend | Google Gemini API Key (stored in secret manager) |
| `GEMINI_MODEL` | Backend | Set to `gemini-3.5-flash-lite` |
| `FASTAPI_HOST` | Backend | Binding interface (e.g. `0.0.0.0`) |
| `FASTAPI_PORT` | Backend | Port number (default `8000`) |
| `PORT` | Frontend | Next.js server port (default `3000`) |
| `NEXT_PUBLIC_API_URL` | Frontend | Optional override for direct API communication |

### 3. High Availability, Health Checks & Monitoring
- **Health Probe**: Automated monitoring via `GET /api/health` returning dataset volume and LLM readiness.
- **Graceful Fallbacks**: If Gemini API limits or network timeouts occur, the backend automatically serves deterministic heuristic recommendations without crashing.
- **Data Persistence**: `data/processed/restaurants.parquet` is embedded into the container image or mounted via an S3/GCS bucket volume, requiring no external relational database.

---

## Cross-Cutting Decisions

### Hybrid retrieval + generation

| Layer | Role |
|-------|------|
| Structured filter | Precision, speed, cost control, grounding |
| LLM | Soft ranking, explanations, free-text preference understanding |

Do **not** send the entire dataset to the LLM.

### Budget mapping

Fixed thresholds (documented in Phase 1):

- `low`: cost_for_two < 500  
- `medium`: 500–1500  
- `high`: > 1500  

### Success definition

1. Enter location, budget, cuisine, min rating, optional notes  
2. Get ranked real restaurants from the HF dataset  
3. See cuisine, rating, cost, and AI explanation per item  
4. Stable empty-result and LLM-failure behavior  
