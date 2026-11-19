"""Validated user preference models for filtering and LLM prompting."""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class BudgetBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_control_chars(text: str) -> str:
    cleaned = _CONTROL_CHARS.sub("", text)
    # Drop other non-printable unicode categories except normal whitespace
    return "".join(
        ch
        for ch in cleaned
        if ch in "\t\n\r" or unicodedata.category(ch)[0] != "C"
    )


class UserPreferences(BaseModel):
    """Canonical preference object consumed by Phase 3 (filter) and Phase 4 (LLM)."""

    location: str = Field(..., min_length=1, description="Locality or area name")
    budget: BudgetBand = Field(..., description="Budget band: low | medium | high")
    cuisine: str = Field(..., min_length=1, description="Preferred cuisine")
    min_rating: float = Field(
        default=3.5,
        ge=0.0,
        le=5.0,
        description="Minimum restaurant rating (0–5)",
    )
    additional: str | None = Field(
        default=None,
        max_length=500,
        description="Optional free-text preferences",
    )

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
        "use_enum_values": False,
    }

    @field_validator("location", "cuisine", mode="before")
    @classmethod
    def _normalize_required_text(cls, value: Any) -> str:
        if value is None:
            raise ValueError("must not be empty")
        text = _strip_control_chars(str(value)).strip()
        if not text:
            raise ValueError("must not be empty")
        return text

    @field_validator("cuisine", mode="after")
    @classmethod
    def _title_case_cuisine(cls, value: str) -> str:
        # Preserve known multi-word casing lightly; title-case tokens
        return ", ".join(part.strip().title() for part in value.split(",") if part.strip())

    @field_validator("additional", mode="before")
    @classmethod
    def _sanitize_additional(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = _strip_control_chars(str(value)).strip()
        return text or None

    @model_validator(mode="after")
    def _normalize_location_display(self) -> UserPreferences:
        # Collapse internal whitespace for stable serialization
        self.location = " ".join(self.location.split())
        return self

    def to_prompt_dict(self) -> dict[str, Any]:
        """Stable dict for Phase 3/4 (JSON-serializable)."""
        return {
            "location": self.location,
            "budget": self.budget.value,
            "cuisine": self.cuisine,
            "min_rating": self.min_rating,
            "additional": self.additional,
        }
