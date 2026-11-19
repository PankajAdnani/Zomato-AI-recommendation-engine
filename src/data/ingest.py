"""
Phase 1 — load Zomato data from Hugging Face, clean, and persist.

Usage (from project root):
    python -m src.data.ingest
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pandas as pd

from src.config import (
    BUDGET_LOW_MAX,
    BUDGET_MEDIUM_MAX,
    HF_DATASET_ID,
)
from src.data.schema import (
    CANONICAL_COLUMNS,
    COLUMN_DESCRIPTIONS,
    RAW_COLUMNS,
    RAW_TO_CANONICAL_RENAME,
)
from src.data.store import save_data_dictionary, save_restaurants


def _make_restaurant_id(name: str, address: str) -> str:
    digest = hashlib.sha1(f"{name}|{address}".encode("utf-8")).hexdigest()
    return digest[:12]


def parse_rating(value: Any) -> float | None:
    """Parse values like '4.1/5', 'NEW', '-', None into a float or None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.upper() in {"NEW", "-", "NAN", "NONE"}:
        return None
    match = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*5$", text)
    if match:
        return float(match.group(1))
    try:
        return float(text)
    except ValueError:
        return None


def parse_cost(value: Any) -> float | None:
    """Parse approx cost strings like '800' or '1,200' into a float."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.upper() in {"NAN", "NONE", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def assign_budget_band(cost: float | None) -> str | None:
    if cost is None or pd.isna(cost):
        return None
    if cost <= BUDGET_LOW_MAX:
        return "low"
    if cost <= BUDGET_MEDIUM_MAX:
        return "medium"
    return "high"


def normalize_cuisines(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    parts = [p.strip() for p in str(value).split(",") if p.strip()]
    if not parts:
        return None
    return ", ".join(parts)


def _clean_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def load_raw_dataframe(dataset_id: str = HF_DATASET_ID) -> pd.DataFrame:
    """Download (or use HF cache) and return the raw train split as a DataFrame."""
    from datasets import load_dataset

    print(f"Loading dataset: {dataset_id}")
    dataset = load_dataset(dataset_id)
    split_name = "train" if "train" in dataset else next(iter(dataset.keys()))
    df = dataset[split_name].to_pandas()
    print(f"Loaded split '{split_name}' with {len(df):,} rows, {len(df.columns)} columns")
    return df


def preprocess(raw: pd.DataFrame) -> pd.DataFrame:
    """Map raw HF columns to the canonical schema and clean values."""
    missing_raw = [c for c in RAW_COLUMNS if c not in raw.columns]
    if missing_raw:
        raise ValueError(f"Dataset missing expected columns: {missing_raw}")

    df = raw[RAW_COLUMNS].copy()
    df = df.rename(columns=RAW_TO_CANONICAL_RENAME)

    for col in ("name", "address", "location", "city", "rest_type", "url"):
        df[col] = df[col].map(_clean_text)

    df["online_order"] = df["online_order"].map(_clean_text)
    df["book_table"] = df["book_table"].map(_clean_text)
    df["listed_in_type"] = df["listed_in_type"].map(_clean_text)
    df["dish_liked"] = df["dish_liked"].map(_clean_text)
    df["cuisines"] = df["cuisines"].map(normalize_cuisines)

    df["rating"] = df["rate"].map(parse_rating)
    df["cost_for_two"] = df["approx_cost(for two people)"].map(parse_cost)
    df["budget_band"] = df["cost_for_two"].map(assign_budget_band)

    df["votes_count"] = pd.to_numeric(df["votes_count"], errors="coerce").fillna(0).astype(int)

    before = len(df)
    df = df.dropna(subset=["name", "location", "rating"])
    dropped_critical = before - len(df)

    df["restaurant_id"] = [
        _make_restaurant_id(n or "", a or "")
        for n, a in zip(df["name"], df["address"].fillna(""))
    ]

    # Deduplicate: same name + location → keep highest votes, then rating
    before_dedup = len(df)
    df = df.sort_values(
        by=["votes_count", "rating"],
        ascending=[False, False],
    )
    df = df.drop_duplicates(subset=["name", "location"], keep="first")
    deduped = before_dedup - len(df)

    df = df.reindex(columns=CANONICAL_COLUMNS).reset_index(drop=True)

    print(
        f"Cleaning: dropped {dropped_critical:,} rows missing name/location/rating; "
        f"removed {deduped:,} duplicates; {len(df):,} rows remain"
    )
    return df


def build_data_dictionary(df: pd.DataFrame, raw_row_count: int) -> dict[str, Any]:
    cuisine_tokens: set[str] = set()
    for value in df["cuisines"].dropna():
        for token in str(value).split(","):
            token = token.strip()
            if token:
                cuisine_tokens.add(token)

    null_rates = {
        col: round(float(df[col].isna().mean()), 4) for col in CANONICAL_COLUMNS
    }

    return {
        "source_dataset": HF_DATASET_ID,
        "raw_row_count": raw_row_count,
        "processed_row_count": len(df),
        "columns": COLUMN_DESCRIPTIONS,
        "budget_bands": {
            "low": f"cost_for_two <= {BUDGET_LOW_MAX}",
            "medium": f"{BUDGET_LOW_MAX + 1} <= cost_for_two <= {BUDGET_MEDIUM_MAX}",
            "high": f"cost_for_two > {BUDGET_MEDIUM_MAX}",
        },
        "null_rates": null_rates,
        "unique_locations": int(df["location"].nunique(dropna=True)),
        "unique_cities": int(df["city"].nunique(dropna=True)),
        "unique_cuisines": len(cuisine_tokens),
        "budget_band_counts": df["budget_band"].value_counts(dropna=False).to_dict(),
        "rating": {
            "min": float(df["rating"].min()),
            "max": float(df["rating"].max()),
            "mean": round(float(df["rating"].mean()), 3),
        },
        "cost_for_two": {
            "min": float(df["cost_for_two"].min(skipna=True))
            if df["cost_for_two"].notna().any()
            else None,
            "max": float(df["cost_for_two"].max(skipna=True))
            if df["cost_for_two"].notna().any()
            else None,
            "median": float(df["cost_for_two"].median(skipna=True))
            if df["cost_for_two"].notna().any()
            else None,
        },
        "sample_rows": df.head(5).to_dict(orient="records"),
    }


def run_ingestion() -> pd.DataFrame:
    raw = load_raw_dataframe()
    processed = preprocess(raw)
    paths = save_restaurants(processed)
    dictionary = build_data_dictionary(processed, raw_row_count=len(raw))
    dict_path = save_data_dictionary(dictionary)

    print(f"Wrote {paths['parquet']}")
    print(f"Wrote {paths['csv']}")
    print(f"Wrote {dict_path}")
    print("\nSample (first 5 rows):")
    print(
        processed[
            ["restaurant_id", "name", "location", "cuisines", "rating", "cost_for_two", "budget_band"]
        ]
        .head(5)
        .to_string(index=False)
    )
    return processed


def main() -> None:
    run_ingestion()


if __name__ == "__main__":
    main()
