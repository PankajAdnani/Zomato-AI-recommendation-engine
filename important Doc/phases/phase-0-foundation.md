# Phase 0 — Project Foundation

> Status: **Scaffolded with Phase 1** (minimal). Expand as later phases need it.  
> Parent: [architecture.md](../architecture.md)

## Objectives

- Establish repository structure, dependencies, environment variables, and coding conventions.
- Define module boundaries before implementing business logic.

## Directory Structure

```
Zomato Restaurant Recommendation System/
├── important Doc/
│   ├── Problem statement.md
│   ├── architecture.md
│   └── phases/
│       ├── phase-0-foundation.md
│       ├── phase-1-data-ingestion.md
│       ├── phase-2-user-input.md
│       ├── phase-3-filtering.md
│       ├── phase-4-llm-engine.md
│       └── phase-5-output-display.md
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data/          # Phase 1
│   ├── preferences/   # Phase 2
│   ├── filtering/     # Phase 3
│   ├── llm/           # Phase 4
│   └── app/           # Phase 5
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Deliverables

- [x] `requirements.txt` (Phase 1 deps)
- [x] `.env.example`
- [x] `src/config.py`
- [ ] Full skeleton for all phases (add when each phase starts)
- [ ] README setup steps (expand in Phase 5)

## Exit Criteria

- [x] Project installs in a clean virtualenv
- [x] Config loads without hard-coded secrets
- [ ] App entrypoint health check (deferred to Phase 5)

## Change Log

| Date | Change |
|------|--------|
| 2026-10-08 | Initial split from architecture.md; minimal scaffold with Phase 1 |
