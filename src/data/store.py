"""Read/write processed restaurant artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    DATA_DICTIONARY_PATH,
    DATA_PROCESSED_DIR,
    PROCESSED_CSV,
    PROCESSED_PARQUET,
)
from src.data.schema import CANONICAL_COLUMNS


def ensure_processed_dir() -> Path:
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED_DIR


def save_restaurants(df: pd.DataFrame) -> dict[str, Path]:
    """Persist restaurants as Parquet and CSV. Returns written paths."""
    ensure_processed_dir()
    ordered = df.reindex(columns=CANONICAL_COLUMNS)
    ordered.to_parquet(PROCESSED_PARQUET, index=False)
    ordered.to_csv(PROCESSED_CSV, index=False)
    return {"parquet": PROCESSED_PARQUET, "csv": PROCESSED_CSV}


def load_restaurants(prefer_parquet: bool = True) -> pd.DataFrame:
    """
    Load processed restaurants offline (no Hugging Face required).

    Prefers Parquet; falls back to CSV if Parquet is missing.
    """
    if prefer_parquet and PROCESSED_PARQUET.exists():
        df = pd.read_parquet(PROCESSED_PARQUET)
    elif PROCESSED_CSV.exists():
        df = pd.read_csv(PROCESSED_CSV)
    elif PROCESSED_PARQUET.exists():
        df = pd.read_parquet(PROCESSED_PARQUET)
    else:
        raise FileNotFoundError(
            "Processed restaurant data not found. "
            "Run: python -m src.data.ingest"
        )

    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Processed data missing columns: {missing}")
    return df.reindex(columns=CANONICAL_COLUMNS)


def save_data_dictionary(payload: dict[str, Any]) -> Path:
    ensure_processed_dir()
    DATA_DICTIONARY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return DATA_DICTIONARY_PATH


def load_data_dictionary() -> dict[str, Any]:
    if not DATA_DICTIONARY_PATH.exists():
        raise FileNotFoundError(
            f"Data dictionary not found at {DATA_DICTIONARY_PATH}. "
            "Run: python -m src.data.ingest"
        )
    return json.loads(DATA_DICTIONARY_PATH.read_text(encoding="utf-8"))
