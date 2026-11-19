"""Orchestration, JSON validation, hallucination checking, and heuristic fallback for recommendations.

LLM backend: Google Gemini (via GeminiClient). Falls back to heuristic ranking when API is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.filtering.engine import CandidateResult
from src.llm.client import GeminiClient
from src.llm.models import RecommendationItem, RecommendationResponse
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.preferences.models import UserPreferences

logger = logging.getLogger(__name__)


def _generate_heuristic_fallback(
    candidate_result: CandidateResult,
    prefs: UserPreferences,
    top_n: int = 5,
    reason_note: str = "Heuristic ranking active (Gemini API unavailable).",
) -> RecommendationResponse:
    """Generate deterministic recommendations using candidate heuristic scores when LLM is offline."""
    df = candidate_result.candidates_df.head(top_n)
    if df.empty:
        return RecommendationResponse(
            summary="No matching restaurants available to recommend.",
            recommendations=[],
            provider="heuristic-fallback",
            model="none",
            is_fallback=True,
        )

    recommendations: list[RecommendationItem] = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        cost_val = row.get("cost_for_two")
        cost_str = f"₹{int(cost_val)} for two" if pd_notna(cost_val) else "Cost unavailable"
        cuisine_str = str(row.get("cuisines", ""))
        rating_val = float(row.get("rating", 0.0))
        votes_val = int(row.get("votes_count", 0))
        loc_str = str(row.get("location", ""))
        name_str = str(row.get("name", ""))
        rest_id = str(row.get("restaurant_id", idx))

        explanation = (
            f"Top match in {loc_str} with {rating_val}★ rating and {votes_val:,} reviews. "
            f"Serves {cuisine_str} fitting your {prefs.budget.value} budget preference."
        )

        item = RecommendationItem(
            restaurant_id=rest_id,
            rank=idx,
            name=name_str,
            cuisine=cuisine_str,
            rating=rating_val,
            estimated_cost=cost_str,
            explanation=explanation,
        )
        recommendations.append(item)

    loc_target = prefs.location
    cuis_target = prefs.cuisine
    summary = (
        f"Selected top {len(recommendations)} {cuis_target} restaurants in {loc_target} "
        f"based on rating, review volume, and budget alignment ({reason_note})."
    )

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        provider="heuristic-fallback",
        model="none",
        is_fallback=True,
    )


def pd_notna(val: Any) -> bool:
    """Check if value is not NaN/None."""
    if val is None:
        return False
    try:
        import pandas as pd
        return bool(pd.notna(val))
    except ImportError:
        return True


def generate_recommendations(
    candidate_result: CandidateResult,
    prefs: UserPreferences,
    top_n: int = 5,
    client: GeminiClient | None = None,
) -> RecommendationResponse:
    """
    Generate ranked recommendations using Gemini LLM with anti-hallucination checks
    and automatic heuristic fallback.
    """
    if candidate_result.candidates_df.empty:
        return RecommendationResponse(
            summary="No candidate restaurants matched your input preferences.",
            recommendations=[],
            provider="none",
            model="none",
            is_fallback=False,
        )

    llm_client = client or GeminiClient()

    if not llm_client.is_available():
        logger.info("Gemini client not available. Using heuristic fallback recommender.")
        return _generate_heuristic_fallback(
            candidate_result,
            prefs,
            top_n=top_n,
            reason_note="Add GEMINI_API_KEY to .env to enable AI explanations",
        )

    # Prepare compact context candidates
    candidates_context = candidate_result.to_llm_context(top_k=20)
    valid_ids = {item["restaurant_id"] for item in candidates_context if "restaurant_id" in item}
    valid_names = {item["name"].lower() for item in candidates_context if "name" in item}

    user_prompt = build_user_prompt(prefs, candidates_context, top_n=top_n)

    try:
        raw_json = llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        data = json.loads(raw_json)

        raw_summary = str(data.get("summary", "Top AI recommendations based on your preferences."))
        raw_recs = data.get("recommendations", [])

        valid_items: list[RecommendationItem] = []
        for rec in raw_recs:
            if not isinstance(rec, dict):
                continue

            r_id = str(rec.get("restaurant_id", ""))
            r_name = str(rec.get("name", ""))

            # Anti-hallucination guard: Verify restaurant exists in candidate list
            if r_id not in valid_ids and r_name.lower() not in valid_names:
                logger.warning(
                    f"Hallucinated recommendation rejected: id='{r_id}', name='{r_name}'"
                )
                continue

            try:
                item = RecommendationItem(
                    restaurant_id=r_id,
                    rank=len(valid_items) + 1,
                    name=r_name,
                    cuisine=str(rec.get("cuisine", "")),
                    rating=float(rec.get("rating", 0.0)),
                    estimated_cost=str(rec.get("estimated_cost", "")),
                    explanation=str(rec.get("explanation", "")),
                )
                valid_items.append(item)
            except Exception as item_err:
                logger.warning(f"Error parsing item schema: {item_err}")
                continue

            if len(valid_items) >= top_n:
                break

        # If LLM returned 0 valid non-hallucinated items, fall back
        if not valid_items:
            logger.warning("LLM response contained zero valid candidates. Falling back to heuristic.")
            return _generate_heuristic_fallback(
                candidate_result,
                prefs,
                top_n=top_n,
                reason_note="LLM response failed validation",
            )

        return RecommendationResponse(
            summary=raw_summary,
            recommendations=valid_items,
            provider=llm_client.provider,
            model=llm_client.model,
            is_fallback=False,
        )

    except Exception as exc:
        logger.error(f"Error during LLM recommendation generation: {exc}")
        return _generate_heuristic_fallback(
            candidate_result,
            prefs,
            top_n=top_n,
            reason_note=f"Gemini API error ({exc})",
        )
