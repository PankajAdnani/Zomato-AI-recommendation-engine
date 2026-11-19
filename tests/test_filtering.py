"""Phase 3 — Candidate filtering engine tests."""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.store import load_restaurants
from src.filtering.engine import (
    CandidateResult,
    compute_heuristic_score,
    filter_restaurants,
)
from src.preferences.models import BudgetBand, UserPreferences


@pytest.fixture
def mock_restaurants_df() -> pd.DataFrame:
    """Synthetic dataset for deterministic unit testing."""
    return pd.DataFrame(
        [
            {
                "restaurant_id": "r1",
                "name": "Pasta Paradise",
                "address": "123 Main St",
                "location": "Koramangala 5th Block",
                "city": "Koramangala",
                "cuisines": "Italian, Pizza",
                "rating": 4.5,
                "votes_count": 500,
                "cost_for_two": 800,
                "budget_band": "medium",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "Yes",
                "listed_in_type": "Dine-out",
                "dish_liked": "Pasta, Tiramisu",
                "url": "http://example.com/r1",
            },
            {
                "restaurant_id": "r2",
                "name": "Cheap Pizza Slice",
                "address": "456 Side St",
                "location": "Koramangala 5th Block",
                "city": "Koramangala",
                "cuisines": "Italian, Fast Food",
                "rating": 3.8,
                "votes_count": 50,
                "cost_for_two": 300,
                "budget_band": "low",
                "rest_type": "Quick Bytes",
                "online_order": "Yes",
                "book_table": "No",
                "listed_in_type": "Delivery",
                "dish_liked": "Pizza",
                "url": "http://example.com/r2",
            },
            {
                "restaurant_id": "r3",
                "name": "Luxury Italian Bistro",
                "address": "789 High St",
                "location": "Indiranagar",
                "city": "Indiranagar",
                "cuisines": "Italian, Fine Dining",
                "rating": 4.8,
                "votes_count": 1200,
                "cost_for_two": 2200,
                "budget_band": "high",
                "rest_type": "Fine Dining",
                "online_order": "No",
                "book_table": "Yes",
                "listed_in_type": "Dine-out",
                "dish_liked": "Risotto, Wine",
                "url": "http://example.com/r3",
            },
            {
                "restaurant_id": "r4",
                "name": "Curry House",
                "address": "101 Spice Rd",
                "location": "Koramangala 5th Block",
                "city": "Koramangala",
                "cuisines": "North Indian, Thali",
                "rating": 4.2,
                "votes_count": 300,
                "cost_for_two": 600,
                "budget_band": "medium",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
                "listed_in_type": "Dine-out",
                "dish_liked": "Butter Chicken",
                "url": "http://example.com/r4",
            },
        ]
    )


def test_strict_filtering_exact_match(mock_restaurants_df: pd.DataFrame):
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
    )
    result = filter_restaurants(mock_restaurants_df, prefs, top_k=10, allow_relaxation=False)

    assert isinstance(result, CandidateResult)
    assert result.total_matched == 1
    assert result.relaxation_level == 0
    assert len(result.candidates_df) == 1
    assert result.candidates_df.iloc[0]["name"] == "Pasta Paradise"


def test_heuristic_scoring_ordering(mock_restaurants_df: pd.DataFrame):
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.MEDIUM,
        cuisine="Italian",
        min_rating=3.0,
    )
    # Both r1 (Pasta Paradise) and r2 (Cheap Pizza Slice - low budget) if budget is medium
    result = filter_restaurants(mock_restaurants_df, prefs, top_k=10, allow_relaxation=False)
    # Only r1 matches strict budget=medium
    assert len(result.candidates_df) == 1
    assert "score" in result.candidates_df.columns
    assert result.candidates_df.iloc[0]["score"] > 0.0


def test_progressive_relaxation_level_1_budget(mock_restaurants_df: pd.DataFrame):
    # Request high budget for Koramangala 5th Block Italian (only r1 medium and r2 low exist there)
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.HIGH,
        cuisine="Italian",
        min_rating=3.5,
    )
    result = filter_restaurants(mock_restaurants_df, prefs, top_k=10, allow_relaxation=True)

    assert result.relaxation_level == 1
    assert len(result.relaxation_notes) == 1
    assert "budget constraint" in result.relaxation_notes[0].lower()
    # Should include r1 and r2 (since budget was relaxed)
    assert len(result.candidates_df) == 2


def test_progressive_relaxation_level_2_rating(mock_restaurants_df: pd.DataFrame):
    # Request min_rating 4.9 in Koramangala 5th Block Italian
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.LOW,
        cuisine="Italian",
        min_rating=4.2,  # r2 low budget has rating 3.8
    )
    result = filter_restaurants(mock_restaurants_df, prefs, top_k=10, allow_relaxation=True)

    # Strict low budget + Italian has rating 3.8 (<4.2). Level 1 relaxes budget -> finds r1 (4.5 rating)
    assert result.total_matched > 0
    assert result.relaxation_level > 0


def test_to_llm_context_formatting(mock_restaurants_df: pd.DataFrame):
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
    )
    result = filter_restaurants(mock_restaurants_df, prefs, top_k=5)
    context = result.to_llm_context(top_k=5)

    assert isinstance(context, list)
    assert len(context) == 1
    item = context[0]
    assert item["restaurant_id"] == "r1"
    assert item["name"] == "Pasta Paradise"
    assert item["rating"] == 4.5
    assert item["budget_band"] == "medium"
    assert "cuisines" in item
    assert "url" in item


def test_empty_dataframe():
    empty_df = pd.DataFrame()
    prefs = UserPreferences(location="BTM", budget="low", cuisine="Chinese")
    result = filter_restaurants(empty_df, prefs)

    assert result.total_matched == 0
    assert len(result.candidates_df) == 0
    assert result.to_llm_context() == []


def test_integration_with_real_dataset():
    df = load_restaurants()
    prefs = UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.MEDIUM,
        cuisine="Italian",
        min_rating=3.5,
    )
    result = filter_restaurants(df, prefs, top_k=20)

    assert result.total_matched > 0
    assert len(result.candidates_df) <= 20
    assert "score" in result.candidates_df.columns
    llm_context = result.to_llm_context(top_k=5)
    assert len(llm_context) <= 5
    assert all("name" in rec for rec in llm_context)
