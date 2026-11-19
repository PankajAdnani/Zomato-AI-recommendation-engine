"""Pydantic schemas for LLM recommendation response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """Single restaurant recommendation item with AI justification."""

    restaurant_id: str = Field(..., description="Unique ID of candidate restaurant")
    rank: int = Field(..., description="1-indexed rank order")
    name: str = Field(..., description="Restaurant display name")
    cuisine: str = Field(..., description="Cuisine type")
    rating: float = Field(..., description="Numeric rating 0-5")
    estimated_cost: str = Field(..., description="Cost description (e.g. ₹800 for two)")
    explanation: str = Field(
        ..., description="Short explanation of why this restaurant matches user preferences"
    )


class RecommendationResponse(BaseModel):
    """Complete recommendation response payload from LLM or fallback engine."""

    summary: str = Field(..., description="Short introductory summary paragraph")
    recommendations: list[RecommendationItem] = Field(
        default_factory=list, description="Ranked list of recommendations"
    )
    provider: str = Field(default="groq", description="LLM provider name or fallback")
    model: str = Field(default="llama-3.3-70b-versatile", description="Model used")
    is_fallback: bool = Field(default=False, description="True if generated via heuristic fallback")
