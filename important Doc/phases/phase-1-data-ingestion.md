# Phase 1 â€” Data Ingestion

> Status: **Implemented**  
> Parent: [architecture.md](../architecture.md)  
> Dataset: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

## Objectives

Load and preprocess the Zomato dataset from Hugging Face and produce a **query-ready** restaurant table.

## Workflow

```
Hugging Face Dataset
        â”‚
        â–¼
   Download / cache
        â”‚
        â–¼
  Column inspection & mapping
        â”‚
        â–¼
  Cleaning & normalization
  (nulls, dtypes, cuisine lists,
   cost bands, location tokens)
        â”‚
        â–¼
  Persist processed artifact
  (Parquet + CSV + data dictionary)
```

## Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Config | `src/config.py` | Paths, dataset id, budget thresholds |
| Schema | `src/data/schema.py` | Raw â†’ canonical column mapping & types |
| Ingest | `src/data/ingest.py` | HF load, clean, normalize, CLI entry |
| Store | `src/data/store.py` | Read/write processed artifacts |

## Raw â†’ Canonical Mapping

| Canonical field | Raw HF column | Notes |
|-----------------|---------------|-------|
| `restaurant_id` | (generated) | Stable hash of `name` + `address` |
| `name` | `name` | Trimmed |
| `address` | `address` | Trimmed |
| `location` | `location` | Locality (e.g. Banashankari) |
| `city` | `listed_in(city)` | Listed city area |
| `cuisines` | `cuisines` | Comma-separated, normalized |
| `rating` | `rate` | Parsed from `"4.1/5"` â†’ `4.1` |
| `votes_count` | `votes` | Integer |
| `cost_for_two` | `approx_cost(for two people)` | Parsed numeric (commas removed) |
| `budget_band` | (derived) | See thresholds below |
| `rest_type` | `rest_type` | e.g. Casual Dining, Cafe |
| `online_order` | `online_order` | Yes/No |
| `book_table` | `book_table` | Yes/No |
| `listed_in_type` | `listed_in(type)` | Buffet, Cafes, etc. |
| `dish_liked` | `dish_liked` | Optional display/LLM context |
| `url` | `url` | Source link |

Heavy columns (`reviews_list`, `menu_item`, `phone`) are **dropped** to keep the processed store lean for filtering + LLM context.

## Budget Band Rules (fixed thresholds)

| Band | Condition (`cost_for_two`) |
|------|----------------------------|
| `low` | `< 500` |
| `medium` | `500` â€“ `1500` (inclusive) |
| `high` | `> 1500` |

## Preprocessing Rules

1. Drop rows missing critical fields: `name`, `location`, `rating`.
2. Normalize text: trim whitespace; keep original casing for display; use lowercased copies only inside match helpers if added later.
3. Parse rating/cost; invalid values â†’ null â†’ row dropped if critical.
4. Deduplicate by `name` + `location` (keep highest `votes_count`, then highest `rating`).
5. Persist `data/processed/data_dictionary.json` with profile stats.

## How to Run

```bash
# from project root
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m src.data.ingest
```

Outputs:

- `data/processed/restaurants.parquet`
- `data/processed/restaurants.csv`
- `data/processed/data_dictionary.json`

Load later (no HF needed):

```python
from src.data.store import load_restaurants
df = load_restaurants()
```

## Exit Criteria

- [x] Dataset loads offline from processed file
- [x] Canonical columns available without HF at runtime
- [x] Sample rows printable in expected schema
- [x] CLI: `python -m src.data.ingest`


## Run Results (2026-10-08)

| Metric | Value |
|--------|-------|
| Raw rows | 51,717 |
| Dropped (missing name/location/rating) | 10,052 |
| Duplicates removed (`name` + `location`) | 32,416 |
| Processed unique restaurants | 9,249 |

> High duplicate count is expected: the HF dump lists the same restaurant under multiple `listed_in(type)` / `listed_in(city)` combinations.
## Change Log

| Date | Change |
|------|--------|
| 2026-10-08 | Initial implementation; split from architecture.md |
| 2026-10-08 | First successful ingest run; 9,249 unique restaurants |

