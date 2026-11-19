"""Phase 2 — preference validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.preferences.models import BudgetBand, UserPreferences


def test_valid_preferences_serialize():
    prefs = UserPreferences(
        location="  Koramangala 5th Block  ",
        budget=BudgetBand.MEDIUM,
        cuisine="italian",
        min_rating=4.0,
        additional="family-friendly",
    )
    assert prefs.location == "Koramangala 5th Block"
    assert prefs.cuisine == "Italian"
    assert prefs.budget == BudgetBand.MEDIUM
    payload = prefs.to_prompt_dict()
    assert payload == {
        "location": "Koramangala 5th Block",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
        "additional": "family-friendly",
    }


def test_default_min_rating():
    prefs = UserPreferences(
        location="BTM",
        budget="low",
        cuisine="Chinese",
    )
    assert prefs.min_rating == 3.5
    assert prefs.additional is None


def test_empty_location_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(location="   ", budget="low", cuisine="Italian")


def test_invalid_budget_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(location="BTM", budget="luxury", cuisine="Italian")


def test_min_rating_bounds():
    with pytest.raises(ValidationError):
        UserPreferences(location="BTM", budget="low", cuisine="Italian", min_rating=5.5)
    with pytest.raises(ValidationError):
        UserPreferences(location="BTM", budget="low", cuisine="Italian", min_rating=-0.1)


def test_additional_sanitized_and_empty_becomes_none():
    prefs = UserPreferences(
        location="BTM",
        budget="high",
        cuisine="BBQ",
        additional="  \x00quick service\x07  ",
    )
    assert prefs.additional == "quick service"

    prefs2 = UserPreferences(
        location="BTM",
        budget="high",
        cuisine="BBQ",
        additional="   ",
    )
    assert prefs2.additional is None


def test_additional_max_length():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="BTM",
            budget="low",
            cuisine="Italian",
            additional="x" * 501,
        )
