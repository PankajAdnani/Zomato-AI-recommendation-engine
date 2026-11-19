"""Vocabulary helpers derived from processed restaurant data (Phase 1)."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.data.store import load_restaurants


@lru_cache(maxsize=1)
def _cached_frame() -> pd.DataFrame:
    return load_restaurants()


def clear_vocab_cache() -> None:
    _cached_frame.cache_clear()


def list_locations() -> list[str]:
    """Sorted unique localities from the processed dataset."""
    df = _cached_frame()
    return sorted(df["location"].dropna().astype(str).str.strip().unique().tolist())


def list_cuisines() -> list[str]:
    """Sorted unique cuisine tokens from the processed dataset."""
    df = _cached_frame()
    tokens: set[str] = set()
    for value in df["cuisines"].dropna().astype(str):
        for part in value.split(","):
            token = part.strip()
            if token:
                tokens.add(token)
    return sorted(tokens)


def list_cities() -> list[str]:
    df = _cached_frame()
    return sorted(df["city"].dropna().astype(str).str.strip().unique().tolist())


def suggest_locations(query: str, limit: int = 8) -> list[str]:
    """Case-insensitive substring matches against known localities."""
    q = (query or "").strip().lower()
    if not q:
        return []
    matches = [loc for loc in list_locations() if q in loc.lower()]
    return matches[:limit]


def resolve_location(query: str) -> str | None:
    """
    Resolve user location to a known locality if possible.

    Order: exact (case-insensitive) → unique substring match → None.
    """
    q = (query or "").strip().lower()
    if not q:
        return None

    locations = list_locations()
    for loc in locations:
        if loc.lower() == q:
            return loc

    partial = [loc for loc in locations if q in loc.lower()]
    if len(partial) == 1:
        return partial[0]
    return None
