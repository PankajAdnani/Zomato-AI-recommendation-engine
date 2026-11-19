"""Phase 4 — Recommendation engine (LLM & Fallback) tests."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.filtering.engine import CandidateResult
from src.llm.client import GroqClient
from src.llm.models import RecommendationItem, RecommendationResponse
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.llm.recommender import generate_recommendations
from src.preferences.models import BudgetBand, UserPreferences


@pytest.fixture
def sample_candidate_result() -> CandidateResult:
    df = pd.DataFrame(
        [
            {
                "restaurant_id": "r101",
                "name": "Trattoria Milano",
                "location": "Koramangala 5th Block",
                "city": "Koramangala",
                "cuisines": "Italian, Pizza",
                "rating": 4.6,
                "votes_count": 850,
                "cost_for_two": 900,
                "budget_band": "medium",
                "rest_type": "Casual Dining",
                "score": 14.5,
            },
            {
                "restaurant_id": "r102",
                "name": "Bella Italia",
                "location": "Koramangala 5th Block",
                "city": "Koramangala",
                "cuisines": "Italian, Pasta",
                "rating": 4.3,
                "votes_count": 420,
                "cost_for_two": 750,
                "budget_band": "medium",
                "rest_type": "Casual Dining",
                "score": 12.8,
            },
        ]
    )
    return CandidateResult(candidates_df=df, total_matched=2, relaxation_level=0)


@pytest.fixture
def sample_preferences() -> UserPreferences:
    return UserPreferences(
        location="Koramangala 5th Block",
        budget=BudgetBand.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        additional="outdoor seating",
    )


def test_prompt_construction(sample_candidate_result: CandidateResult, sample_preferences: UserPreferences):
    context = sample_candidate_result.to_llm_context()
    user_prompt = build_user_prompt(sample_preferences, context, top_n=3)

    assert "Koramangala 5th Block" in user_prompt
    assert "Italian" in user_prompt
    assert "Trattoria Milano" in user_prompt
    assert "outdoor seating" in user_prompt
    assert SYSTEM_PROMPT.startswith("You are an expert culinary AI guide")


def test_heuristic_fallback_when_api_key_missing(
    sample_candidate_result: CandidateResult, sample_preferences: UserPreferences
):
    # Pass client without API key
    dummy_client = GroqClient(api_key="")
    response = generate_recommendations(
        sample_candidate_result, sample_preferences, top_n=2, client=dummy_client
    )

    assert isinstance(response, RecommendationResponse)
    assert response.is_fallback is True
    assert response.provider == "heuristic-fallback"
    assert len(response.recommendations) == 2
    assert response.recommendations[0].name == "Trattoria Milano"
    assert response.recommendations[0].restaurant_id == "r101"
    assert "₹900 for two" in response.recommendations[0].estimated_cost


def test_mock_groq_client_success(
    sample_candidate_result: CandidateResult, sample_preferences: UserPreferences
):
    mock_json_response = json.dumps(
        {
            "summary": "Here are the top authentic Italian spots in Koramangala.",
            "recommendations": [
                {
                    "restaurant_id": "r101",
                    "rank": 1,
                    "name": "Trattoria Milano",
                    "cuisine": "Italian, Pizza",
                    "rating": 4.6,
                    "estimated_cost": "₹900 for two",
                    "explanation": "Top rated Italian place in Koramangala with outdoor seating options.",
                }
            ],
        }
    )

    mock_client = MagicMock(spec=GroqClient)
    mock_client.is_available.return_value = True
    mock_client.provider = "groq"
    mock_client.model = "llama-3.3-70b-versatile"
    mock_client.generate_json.return_value = mock_json_response

    response = generate_recommendations(
        sample_candidate_result, sample_preferences, top_n=2, client=mock_client
    )

    assert isinstance(response, RecommendationResponse)
    assert response.is_fallback is False
    assert response.provider == "groq"
    assert len(response.recommendations) == 1
    rec = response.recommendations[0]
    assert rec.restaurant_id == "r101"
    assert rec.name == "Trattoria Milano"
    assert rec.rating == 4.6


def test_anti_hallucination_filter(
    sample_candidate_result: CandidateResult, sample_preferences: UserPreferences
):
    # LLM returns one valid candidate (r101) and one hallucinated candidate (r999 Fake Bistro)
    mock_json_response = json.dumps(
        {
            "summary": "Top choices",
            "recommendations": [
                {
                    "restaurant_id": "r999",
                    "rank": 1,
                    "name": "Fake Imaginary Bistro",
                    "cuisine": "Italian",
                    "rating": 5.0,
                    "estimated_cost": "₹1000",
                    "explanation": "Hallucinated entry",
                },
                {
                    "restaurant_id": "r101",
                    "rank": 2,
                    "name": "Trattoria Milano",
                    "cuisine": "Italian",
                    "rating": 4.6,
                    "estimated_cost": "₹900",
                    "explanation": "Valid candidate",
                },
            ],
        }
    )

    mock_client = MagicMock(spec=GroqClient)
    mock_client.is_available.return_value = True
    mock_client.provider = "groq"
    mock_client.model = "llama-3.3-70b-versatile"
    mock_client.generate_json.return_value = mock_json_response

    response = generate_recommendations(
        sample_candidate_result, sample_preferences, top_n=2, client=mock_client
    )

    assert response.is_fallback is False
    assert len(response.recommendations) == 1
    # Hallucinated r999 should be dropped!
    assert response.recommendations[0].restaurant_id == "r101"
    assert response.recommendations[0].rank == 1  # Re-indexed to 1


def test_invalid_json_triggers_fallback(
    sample_candidate_result: CandidateResult, sample_preferences: UserPreferences
):
    mock_client = MagicMock(spec=GroqClient)
    mock_client.is_available.return_value = True
    mock_client.generate_json.side_effect = RuntimeError("API rate limit exceeded")

    response = generate_recommendations(
        sample_candidate_result, sample_preferences, top_n=2, client=mock_client
    )

    assert response.is_fallback is True
    assert response.provider == "heuristic-fallback"
    assert len(response.recommendations) == 2
