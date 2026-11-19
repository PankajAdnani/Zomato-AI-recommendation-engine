# Phase 3 — Integration / Filtering Layer

> Status: **Implemented**  
> Parent: [architecture.md](../architecture.md)  
> Depends on: [Phase 1](phase-1-data-ingestion.md), [Phase 2](phase-2-user-input.md)

## Objectives

Turn preferences into a **structured candidate set** before calling the LLM. Reduces cost, latency, and hallucination risk.

## Workflow

```
UserPreferences
      │
      ▼
 Location → Cuisine → Budget → Rating filters
      │
      ▼
 Soft ranking / heuristic score
      │
      ▼
 Top-K candidates (e.g. K = 15–30)
      │
      ▼
 Compact JSON/table for LLM context
```

## Filter Semantics

| Preference | Behavior |
|------------|----------|
| Location | Exact/contains on `location` or `city`; fuzzy fallback |
| Cuisine | Token/substring match on `cuisines` |
| Budget | Match `budget_band` |
| Min rating | `rating >= min_rating` |
| Additional | Soft — pass to LLM |

## Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Filter engine | `src/filtering/engine.py` | Multi-stage filtering, heuristic score, Top-K, progressive relaxation |

## Failure Modes

| Case | Behavior |
|------|----------|
| Zero matches | Progressive relaxation (budget -> rating -> location) |
| Too many | Top-K sorted by heuristic score |
| Ambiguous location | Vocab resolution / fallback |

## Exit Criteria

- [x] Deterministic candidate sets for sample prefs
- [x] Payload size fit for LLM context
- [x] Empty-result handling

## Change Log

| Date | Change |
|------|--------|
| 2026-10-08 | Doc split from architecture.md |
| 2026-10-09 | Implemented filter engine, progressive relaxation, unit tests, and Streamlit UI candidate preview |

