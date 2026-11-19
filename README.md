# 🍽️ Zomato Restaurant Recommendation System

AI-powered restaurant recommendation engine built on the Hugging Face Zomato dataset, multi-criteria candidate filtering, progressive constraint relaxation, and Google Gemini LLM reasoning (`gemini-3.5-flash-lite`), featuring a decoupled **Next.js 16** frontend and **FastAPI** backend.

---

## 🌟 Key Features

- **Hugging Face Data Ingestion**: Cleaned & deduplicated offline dataset (9,249 unique restaurants from 51,717 raw listings in Bengaluru).
- **Strict Preference Model**: Pydantic validation for `location`, `budget`, `cuisine`, `min_rating`, and sanitized free-text preferences.
- **Candidate Filtering & Ranking Engine**: Multi-criteria filtering combined with heuristic scoring:
  $$\text{Score} = (\text{rating} \times 2.0) + \log_{10}(1 + \text{votes\_count}) + \text{locality\_bonus} + \text{exact\_cuisine\_bonus}$$
- **Progressive Constraint Relaxation**: Multi-tier fallback strategy (budget $\rightarrow$ rating threshold $\rightarrow$ city location expansion) if strict criteria return 0 matches.
- **Google Gemini LLM Reasoning**: Fast AI recommendations using Google Gemini (`gemini-3.5-flash-lite`) with structured JSON validation and anti-hallucination checks.
- **Heuristic Fallback Engine**: Automatic non-LLM fallback if `GEMINI_API_KEY` is missing or API limits are reached.
- **Modern Next.js Frontend**: Authentic Zomato design system with active live search across all 9,249+ restaurants, dish inspiration carousels, brand legends, latency dashboards, and direct Zomato listing URLs.
- **High-Throughput FastAPI Server**: Asynchronous REST API serving `/api/health`, `/api/metadata`, `/api/search`, `/api/trending`, and `/api/recommend`.

---

## 📂 Project Architecture

```text
Zomato Restaurant Recommendation System/
├── frontend/                # Next.js 16 (React 19, TypeScript, Tailwind CSS)
│   ├── src/app/             # Pages, layouts, and global styles
│   ├── next.config.ts       # API proxy rewrites to FastAPI backend
│   ├── package.json         # Frontend dependencies
│   └── Dockerfile           # Multi-stage production container
├── data/
│   ├── raw/                 # Raw HF dataset cache
│   └── processed/           # Processed restaurants (Parquet + CSV, 9,249 records)
├── important Doc/           # System architecture & phase documentation
│   ├── Problem statement.md
│   ├── architecture.md      # Core architecture & deployment topology
│   └── phases/              # Phase 0 to Phase 6 specifications
│       └── phase-6-deployment.md
├── src/
│   ├── api/                 # FastAPI REST server & schemas (server.py)
│   ├── config.py            # System configuration & environment paths
│   ├── data/                # Data ingestion, schema, and storage loader
│   ├── preferences/         # Pydantic preference models & vocab resolution
│   ├── filtering/           # Filtering engine, scoring, & progressive relaxation
│   └── llm/                 # Gemini client, prompts, & anti-hallucination recommender
├── tests/                   # Pytest automated test suite (24 tests)
├── Dockerfile.backend       # Production container for FastAPI server
├── docker-compose.yml       # Multi-container orchestration (Frontend + Backend)
├── .env                     # Local environment file (git-ignored)
├── .env.example             # Template for environment variables
├── requirements.txt         # Python project dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Installation

Clone the repository and set up your Python environment:

```bash
# Set up Python virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt
pip install fastapi uvicorn httpx

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Setup

Create or edit your local `.env` file in the root directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

> Note: If no API key is provided, the system automatically runs in **Heuristic Fallback Mode**.

### 3. Run Locally

#### Option A: Run Both Services Separately

Terminal 1 (Backend API):
```bash
.venv\Scripts\python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 (Next.js Frontend):
```bash
npm --prefix frontend run dev
```

Visit the application at **`http://localhost:3000`** (FastAPI docs at `http://127.0.0.1:8000/docs`).

#### Option B: Run via Docker Compose (Recommended for Production)

```bash
docker compose up --build
```

---

## 🚢 Deployment & Production Architecture

A dedicated deployment specification is maintained in [important Doc/phases/phase-6-deployment.md](importantDoc/phases/phase-6-deployment.md) and [important Doc/architecture.md](importantDoc/architecture.md).

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     Edge / Ingress Layer                               │
│        (Cloudflare / AWS CloudFront / Nginx / Vercel Edge)             │
│        • SSL/TLS Termination (:443)                                    │
│        • Global CDN Caching & Edge Optimization                        │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
    Routes to Frontend (:3000)                       │ Proxies /api/* (:8000)
                    ▼                                ▼
┌────────────────────────────────────────┐ ┌─────────────────────────────┐
│       Next.js Frontend Container       │ │  FastAPI Backend Container  │
│       • Node.js 20/24 Alpine           │ │  • Python 3.11-slim         │
│       • Standalone output mode         │ │  • Uvicorn ASGI Server      │
└────────────────────────────────────────┘ └──────────────┬──────────────┘
                                                          │
                                         ┌────────────────┴──────────────┐
                                         │  Read-Only Data Volume Mount  │
                                         │  • restaurants.parquet        │
                                         └───────────────────────────────┘
```

### Production Deployment Strategies

1. **Unified Containerized Orchestration (AWS ECS / GCP Cloud Run / Render / Railway)**:
   - Multi-container setup managed via `docker-compose.yml`.
   - Backend exposes healthcheck probe at `/api/health`.
   - Frontend leverages Next.js `standalone` output for ultra-lightweight containers (< 100MB).

2. **Decoupled Serverless / Edge Deployment (Vercel + Cloud Run)**:
   - **Frontend**: Deployed to **Vercel** with global edge CDN distribution and microsecond TTFB.
   - **Backend**: Container deployed to **GCP Cloud Run** or **AWS App Runner** scaling to zero on idle.
   - **Zero-CORS**: `next.config.ts` rewrites transparently route `/api/:path*` to the backend URL without CORS preflight penalties.

---

## 🧪 Running Automated Tests

Run the full pytest suite across all modules:

```bash
python -m pytest tests/ -v
```

All **24 test cases** pass, verifying:
- FastAPI API endpoints (health, metadata, trending, search, recommend)
- Preference validation & budget mapping
- Candidate filtering, scoring & progressive relaxation
- Anti-hallucination filtering & Gemini LLM response parsing
- Heuristic fallback mode

---

## 📄 Phase Documentation

- [Problem Statement](importantDoc/Problem%20statement.md)
- [Architecture Overview](importantDoc/architecture.md)
- [Phase 0 — Project Foundation](importantDoc/phases/phase-0-foundation.md)
- [Phase 1 — Data Ingestion](importantDoc/phases/phase-1-data-ingestion.md)
- [Phase 2 — User Input & Preference Model](importantDoc/phases/phase-2-user-input.md)
- [Phase 3 — Integration / Filtering Layer](importantDoc/phases/phase-3-filtering.md)
- [Phase 4 — Recommendation Engine (LLM)](importantDoc/phases/phase-4-llm-engine.md)
- [Phase 5 — Output Display & Productization](importantDoc/phases/phase-5-output-display.md)
- [Phase 6 — Deployment & Production Architecture](importantDoc/phases/phase-6-deployment.md)
