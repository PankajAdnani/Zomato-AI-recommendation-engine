# Phase 2 — User Input & Preference Model

> Status: **Implemented**  
> Parent: [architecture.md](../architecture.md)  
> Depends on: [Phase 1](phase-1-data-ingestion.md)

## Objectives

Collect and validate user preferences that drive filtering and LLM prompting.

## Preference Schema

```text
UserPreferences
├── location: str          # e.g. "Banashankari", "Koramangala 5th Block"
├── budget: enum           # low | medium | high
├── cuisine: str           # e.g. "Italian", "Chinese"
├── min_rating: float      # default 3.5; range 0–5
└── additional: str | null # free text; max 500 chars; sanitized
```

## Validation Rules

| Field | Rules |
|-------|-------|
| `location` | Required; non-empty; whitespace collapsed; fuzzy-resolved via vocab when possible |
| `budget` | Required; one of `low`, `medium`, `high` |
| `cuisine` | Required; tokens title-cased |
| `min_rating` | 0–5; default `3.5` |
| `additional` | Optional; max 500; control chars stripped; blank → `null` |

## Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Preference models | `src/preferences/models.py` | Pydantic `UserPreferences` + `BudgetBand` |
| Vocab helpers | `src/preferences/vocab.py` | Locations/cuisines from Phase 1 data |
| Streamlit UI | `src/app/main.py` | Preference form (echo / debug mode) |
| Tests | `tests/test_preferences.py` | Validation edge cases |

## How to Run

```bash
# from project root (venv activated)
streamlit run src/app/main.py
pytest tests/test_preferences.py -v
```

Echo mode shows the validated JSON / `to_prompt_dict()` payload — no filtering or LLM yet.

## Deliverables

- [x] Validated preference object
- [x] UI echo/debug mode (no LLM)
- [x] Unit tests for invalid inputs

## Exit Criteria

- [x] Invalid inputs rejected with clear messages
- [x] Valid preferences serialize consistently for Phase 3 & 4

## Change Log

| Date | Change |
|------|--------|
| 2026-10-08 | Doc split from architecture.md |
| 2026-10-09 | Implemented models, vocab, Streamlit echo UI, tests |
