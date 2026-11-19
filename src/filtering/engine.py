"""
Phase 3 — Integration / Candidate Filtering Layer.

Turns UserPreferences into a structured, heuristic-ranked candidate set
for LLM context ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.data.schema import CANONICAL_COLUMNS
from src.preferences.models import UserPreferences
from src.preferences.vocab import resolve_location


@dataclass
class CandidateResult:
    """Container for filtered candidate restaurants and relaxation diagnostics."""

    candidates_df: pd.DataFrame
    total_matched: int
    relaxation_level: int = 0
    relaxation_notes: list[str] = field(default_factory=list)

    def to_llm_context(self, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        Convert top candidates into a compact dictionary representation
        optimized for LLM prompt context length.
        """
        df = self.candidates_df
        if top_k is not None:
            df = df.head(top_k)

        records: list[dict[str, Any]] = []
        for idx, row in df.iterrows():
            record = {
                "restaurant_id": str(row.get("restaurant_id", idx)),
                "name": str(row.get("name", "")),
                "location": str(row.get("location", "")),
                "city": str(row.get("city", "")),
                "cuisines": str(row.get("cuisines", "")),
                "rating": float(row.get("rating", 0.0)),
                "votes_count": int(row.get("votes_count", 0)),
                "cost_for_two": int(row.get("cost_for_two", 0)) if pd.notna(row.get("cost_for_two")) else None,
                "budget_band": str(row.get("budget_band", "")),
                "rest_type": str(row.get("rest_type", "")),
                "dish_liked": str(row.get("dish_liked", "")) if pd.notna(row.get("dish_liked")) else "",
                "online_order": str(row.get("online_order", "")),
                "book_table": str(row.get("book_table", "")),
                "url": str(row.get("url", "")),
            }
            records.append(record)
        return records

    def to_dict(self) -> dict[str, Any]:
        """Summary representation of filtering results."""
        return {
            "total_matched": self.total_matched,
            "returned_count": len(self.candidates_df),
            "relaxation_level": self.relaxation_level,
            "relaxation_notes": self.relaxation_notes,
            "top_candidates": [
                {
                    "name": row.get("name"),
                    "location": row.get("location"),
                    "rating": row.get("rating"),
                    "cost_for_two": row.get("cost_for_two"),
                    "score": round(float(row.get("score", 0.0)), 2),
                }
                for _, row in self.candidates_df.head(5).iterrows()
            ],
        }


def compute_heuristic_score(
    df: pd.DataFrame,
    target_location: str,
    target_cuisine: str,
) -> pd.Series:
    """
    Calculate a heuristic relevance score for candidate restaurants.

    Factors:
    - Base rating (rating * 2.0)
    - Popularity log-scale (log1p(votes_count))
    - Exact locality match bonus (+2.0)
    - Exact primary cuisine match bonus (+1.5)
    """
    if df.empty:
        return pd.Series(dtype=float)

    rating_component = df["rating"].fillna(0.0) * 2.0
    votes_component = np.log1p(df["votes_count"].fillna(0).astype(float))

    loc_lower = target_location.strip().lower()
    locality_exact = df["location"].astype(str).str.lower() == loc_lower
    locality_bonus = np.where(locality_exact, 2.0, 0.0)

    cuisine_lower = target_cuisine.strip().lower()
    # Check if target cuisine is listed first (primary cuisine)
    primary_cuisine = (
        df["cuisines"]
        .astype(str)
        .str.split(",")
        .str[0]
        .str.strip()
        .str.lower()
        == cuisine_lower
    )
    cuisine_bonus = np.where(primary_cuisine, 1.5, 0.0)

    score = rating_component + votes_component + locality_bonus + cuisine_bonus
    return pd.Series(score, index=df.index)


def _match_location_mask(df: pd.DataFrame, target_loc: str) -> pd.Series:
    """Build boolean mask matching locality or city area."""
    if not target_loc:
        return pd.Series(True, index=df.index)

    loc_clean = target_loc.strip().lower()
    loc_mask = df["location"].astype(str).str.lower().str.contains(loc_clean, regex=False)
    city_mask = df["city"].astype(str).str.lower().str.contains(loc_clean, regex=False)
    return loc_mask | city_mask


def _match_cuisine_mask(df: pd.DataFrame, target_cuisine: str) -> pd.Series:
    """Build boolean mask matching cuisine substring."""
    if not target_cuisine:
        return pd.Series(True, index=df.index)

    c_clean = target_cuisine.strip().lower()
    return df["cuisines"].astype(str).str.lower().str.contains(c_clean, regex=False)


def filter_restaurants(
    df: pd.DataFrame,
    prefs: UserPreferences,
    top_k: int = 20,
    allow_relaxation: bool = True,
) -> CandidateResult:
    """
    Filter dataframe according to user preferences and score top K candidates.

    Applies progressive relaxation if zero matches are found and allow_relaxation is True.
    """
    if df.empty:
        return CandidateResult(
            candidates_df=pd.DataFrame(columns=CANONICAL_COLUMNS),
            total_matched=0,
            relaxation_level=0,
            relaxation_notes=["Dataframe is empty."],
        )

    # Use resolved location or raw preference location
    target_loc = resolve_location(prefs.location) or prefs.location
    target_cuisine = prefs.cuisine
    target_budget = prefs.budget.value
    target_min_rating = prefs.min_rating

    # Pre-calculate base masks
    loc_mask = _match_location_mask(df, target_loc)
    cuisine_mask = _match_cuisine_mask(df, target_cuisine)
    budget_mask = df["budget_band"] == target_budget
    rating_mask = df["rating"] >= target_min_rating

    # Level 0: Strict filtering
    strict_mask = loc_mask & cuisine_mask & budget_mask & rating_mask
    matched_df = df[strict_mask].copy()

    relaxation_level = 0
    notes: list[str] = []

    # Progressive relaxation steps if empty
    if matched_df.empty and allow_relaxation:
        # Level 1: Relax budget constraint
        level1_mask = loc_mask & cuisine_mask & rating_mask
        matched_df = df[level1_mask].copy()

        if not matched_df.empty:
            relaxation_level = 1
            notes.append(
                f"Relaxed budget constraint (requested '{target_budget}')."
            )
        else:
            # Level 2: Relax rating threshold by 0.5 stars
            relaxed_rating = max(0.0, target_min_rating - 0.5)
            level2_mask = loc_mask & cuisine_mask & (df["rating"] >= relaxed_rating)
            matched_df = df[level2_mask].copy()

            if not matched_df.empty:
                relaxation_level = 2
                notes.append(
                    f"Relaxed budget constraint and lowered min_rating threshold from {target_min_rating} to {relaxed_rating:.1f}."
                )
            else:
                # Level 3: Relax location constraint (match cuisine across all locations)
                level3_mask = cuisine_mask & (df["rating"] >= max(0.0, target_min_rating - 1.0))
                matched_df = df[level3_mask].copy()

                if not matched_df.empty:
                    relaxation_level = 3
                    notes.append(
                        f"Expanded location search beyond '{target_loc}' and relaxed budget/rating filters."
                    )
                else:
                    relaxation_level = 4
                    notes.append("No matching restaurants found even after progressive relaxation.")

    total_matched = len(matched_df)
    if matched_df.empty:
        empty_df = matched_df.reindex(columns=list(CANONICAL_COLUMNS) + ["score"])
        return CandidateResult(
            candidates_df=empty_df,
            total_matched=0,
            relaxation_level=relaxation_level,
            relaxation_notes=notes,
        )

    # Compute heuristic scores for matched candidates
    scores = compute_heuristic_score(matched_df, target_loc, target_cuisine)
    matched_df["score"] = scores

    # Sort candidates by score (descending), rating (descending), votes_count (descending)
    sorted_df = matched_df.sort_values(
        by=["score", "rating", "votes_count"],
        ascending=[False, False, False],
    )

    # Slice top_k
    top_candidates = sorted_df.head(top_k).copy()

    return CandidateResult(
        candidates_df=top_candidates,
        total_matched=total_matched,
        relaxation_level=relaxation_level,
        relaxation_notes=notes,
    )
