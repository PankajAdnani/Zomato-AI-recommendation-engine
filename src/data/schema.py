"""Canonical restaurant schema and raw Hugging Face column mapping."""

from __future__ import annotations

from typing import Final

# Raw HF columns we keep (others are dropped to keep the store lean)
RAW_COLUMNS: Final[list[str]] = [
    "url",
    "address",
    "name",
    "online_order",
    "book_table",
    "rate",
    "votes",
    "location",
    "rest_type",
    "dish_liked",
    "cuisines",
    "approx_cost(for two people)",
    "listed_in(type)",
    "listed_in(city)",
]

# Canonical column order for processed artifacts
CANONICAL_COLUMNS: Final[list[str]] = [
    "restaurant_id",
    "name",
    "address",
    "location",
    "city",
    "cuisines",
    "rating",
    "votes_count",
    "cost_for_two",
    "budget_band",
    "rest_type",
    "online_order",
    "book_table",
    "listed_in_type",
    "dish_liked",
    "url",
]

COLUMN_DESCRIPTIONS: Final[dict[str, str]] = {
    "restaurant_id": "Stable hash id derived from name + address",
    "name": "Restaurant display name",
    "address": "Full street address",
    "location": "Locality / neighborhood",
    "city": "Listed city area from listed_in(city)",
    "cuisines": "Comma-separated cuisine list (normalized spacing)",
    "rating": "Numeric rating on a 0–5 scale (parsed from rate)",
    "votes_count": "Number of votes / reviews",
    "cost_for_two": "Approximate cost for two people (INR)",
    "budget_band": "Derived band: low | medium | high",
    "rest_type": "Restaurant type (e.g. Casual Dining, Cafe)",
    "online_order": "Whether online ordering is available (Yes/No)",
    "book_table": "Whether table booking is available (Yes/No)",
    "listed_in_type": "Zomato listing type (Buffet, Cafes, etc.)",
    "dish_liked": "Popular dishes (may be empty)",
    "url": "Zomato listing URL",
}

RAW_TO_CANONICAL_RENAME: Final[dict[str, str]] = {
    "votes": "votes_count",
    "listed_in(type)": "listed_in_type",
    "listed_in(city)": "city",
}
