"""
FastAPI Backend Server for Zomato Restaurant Recommendation System.
Serves restaurant data, metadata, search queries, and Gemini AI recommendations
to the Next.js frontend.
"""

from __future__ import annotations

import html
import time
from typing import Any, Optional
from pathlib import Path
import sys

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.data.store import load_restaurants
from src.filtering.engine import filter_restaurants
from src.llm.client import GeminiClient
from src.llm.recommender import generate_recommendations
from src.preferences.models import BudgetBand, UserPreferences
from src.preferences.vocab import list_cuisines, list_locations, resolve_location

# Image mapping for high-res culinary images
RESTAURANT_NAME_IMAGE_MAP: dict[str, str] = {
    "byg brewski": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=600&auto=format&fit=crop&q=80",
    "absolute barbecues": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
    "asia kitchen": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&auto=format&fit=crop&q=80",
    "mainland china": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&auto=format&fit=crop&q=80",
    "empire restaurant": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80",
    "nandhana palace": "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=600&auto=format&fit=crop&q=80",
    "meghana foods": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    "beijing bites": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&auto=format&fit=crop&q=80",
    "mcdonald's": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "truffles": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=600&auto=format&fit=crop&q=80",
    "toit": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=600&auto=format&fit=crop&q=80",
    "corner house": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&auto=format&fit=crop&q=80",
}

CUISINE_IMAGE_MAP: dict[str, str] = {
    "biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
    "north indian": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80",
    "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "south indian": "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=600&auto=format&fit=crop&q=80",
    "chinese": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&auto=format&fit=crop&q=80",
    "rolls": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
    "cafe": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=600&auto=format&fit=crop&q=80",
    "desserts": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
    "ice cream": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&auto=format&fit=crop&q=80",
    "bbq": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
    "asian": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&auto=format&fit=crop&q=80",
    "continental": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
    "fast food": "https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=600&auto=format&fit=crop&q=80",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=80"


def get_restaurant_image(name: str = "", cuisines: str = "") -> str:
    n_lower = name.lower()
    for brand_key, img_url in RESTAURANT_NAME_IMAGE_MAP.items():
        if brand_key in n_lower:
            return img_url

    c_lower = cuisines.lower()
    segments = [seg.strip() for seg in c_lower.split(",") if seg.strip()]
    for seg in segments:
        for key, img_url in CUISINE_IMAGE_MAP.items():
            if key == seg or key in seg:
                return img_url

    for key, img_url in CUISINE_IMAGE_MAP.items():
        if key in c_lower:
            return img_url

    return DEFAULT_IMAGE


# Initialize FastAPI app
app = FastAPI(
    title="Zomato Restaurant Recommendation API",
    description="Backend API powering the Next.js Zomato AI Guide Frontend",
    version="2.0.0",
)

# Enable CORS for Next.js frontend (ports 3000, 3001, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dataset & vocabulary cache
_df_cache: Optional[pd.DataFrame] = None
_locations_cache: Optional[list[str]] = None
_cuisines_cache: Optional[list[str]] = None


def get_data() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        _df_cache = load_restaurants()
    return _df_cache


def get_vocab() -> tuple[list[str], list[str]]:
    global _locations_cache, _cuisines_cache
    if _locations_cache is None or _cuisines_cache is None:
        _locations_cache = list_locations()
        _cuisines_cache = list_cuisines()
    return _locations_cache, _cuisines_cache


# Request / Response Schemas
class RecommendRequest(BaseModel):
    location: str
    budget: str = "medium"
    cuisine: str = "North Indian"
    min_rating: float = 3.8
    additional: Optional[str] = None
    top_n: int = 4


class RestaurantItem(BaseModel):
    restaurant_id: str
    name: str
    location: str
    cuisines: str
    rating: float
    votes_count: int
    cost_for_two: Optional[float] = None
    dish_liked: Optional[str] = None
    url: str
    image_url: str


class RecommendationCard(BaseModel):
    restaurant_id: str
    name: str
    cuisines: str
    location: str
    rating: float
    cost_for_two: Optional[float] = None
    why_recommended: str
    highlights: list[str]
    must_try_dishes: list[str]
    url: str
    image_url: str


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationCard]
    metrics: dict[str, Any]
    candidate_count: int


@app.get("/api/health")
def health_check():
    df = get_data()
    locations, _ = get_vocab()
    return {
        "status": "ok",
        "service": "Zomato Recommendation Engine",
        "restaurants_count": len(df),
        "localities_count": len(locations),
        "llm_model": "gemini-3.5-flash-lite",
    }


@app.get("/api/metadata")
def get_metadata():
    df = get_data()
    locations, cuisines = get_vocab()
    return {
        "total_restaurants": len(df),
        "total_localities": len(locations),
        "total_cuisines": len(cuisines),
        "locations": locations,
        "cuisines": cuisines,
        "budget_bands": [
            {"value": "low", "label": "Low (< ₹500 for two)"},
            {"value": "medium", "label": "Medium (₹500–1500 for two)"},
            {"value": "high", "label": "High (> ₹1500 for two)"},
        ],
    }


@app.get("/api/search")
def search_restaurants(q: str = Query("", min_length=1), limit: int = 15):
    df = get_data()
    q_str = q.strip().lower()
    if not q_str:
        return {"query": q, "total_found": 0, "results": []}

    mask = (
        df["name"].astype(str).str.lower().str.contains(q_str, regex=False, na=False)
        | df["cuisines"].astype(str).str.lower().str.contains(q_str, regex=False, na=False)
        | df["location"].astype(str).str.lower().str.contains(q_str, regex=False, na=False)
        | df["dish_liked"].astype(str).str.lower().str.contains(q_str, regex=False, na=False)
    )
    matched_df = df[mask].sort_values(by=["rating", "votes_count"], ascending=[False, False])
    total_found = len(matched_df)

    results = []
    for _, r in matched_df.head(limit).iterrows():
        r_name = str(r["name"])
        r_cuisines = str(r.get("cuisines", ""))
        dish = str(r.get("dish_liked", "")).strip() if pd.notna(r.get("dish_liked")) and str(r.get("dish_liked", "")).strip() != "None" else None
        results.append(
            RestaurantItem(
                restaurant_id=str(r["restaurant_id"]),
                name=r_name,
                location=str(r.get("location", "")),
                cuisines=r_cuisines,
                rating=float(r.get("rating", 4.0)) if pd.notna(r.get("rating")) else 4.0,
                votes_count=int(r.get("votes_count", 0)) if pd.notna(r.get("votes_count")) else 0,
                cost_for_two=float(r["cost_for_two"]) if pd.notna(r.get("cost_for_two")) else None,
                dish_liked=dish,
                url=str(r.get("url", "")),
                image_url=get_restaurant_image(r_name, r_cuisines),
            )
        )

    return {
        "query": q,
        "total_found": total_found,
        "results": [res.model_dump() for res in results],
    }


@app.get("/api/trending")
def get_trending():
    df = get_data()
    trending_candidates = []
    for target_name in ["Byg Brewski", "Absolute Barbecues", "Asia Kitchen"]:
        match = df[df["name"].str.contains(target_name, case=False, na=False)]
        if not match.empty:
            trending_candidates.append(match.iloc[0])

    if len(trending_candidates) < 3:
        top_slice = df.sort_values(by=["rating", "votes_count"], ascending=[False, False]).head(3)
        trending_candidates = [r for _, r in top_slice.iterrows()]

    results = []
    for r in trending_candidates:
        r_name = str(r["name"])
        r_cuisines = str(r.get("cuisines", ""))
        dish = str(r.get("dish_liked", "")).strip() if pd.notna(r.get("dish_liked")) and str(r.get("dish_liked", "")).strip() != "None" else None
        results.append(
            RestaurantItem(
                restaurant_id=str(r["restaurant_id"]),
                name=r_name,
                location=str(r.get("location", "")),
                cuisines=r_cuisines,
                rating=float(r.get("rating", 4.0)) if pd.notna(r.get("rating")) else 4.0,
                votes_count=int(r.get("votes_count", 0)) if pd.notna(r.get("votes_count")) else 0,
                cost_for_two=float(r["cost_for_two"]) if pd.notna(r.get("cost_for_two")) else None,
                dish_liked=dish,
                url=str(r.get("url", "")),
                image_url=get_restaurant_image(r_name, r_cuisines),
            )
        )

    return {"trending": [res.model_dump() for res in results]}


@app.post("/api/recommend", response_model=RecommendResponse)
def get_recommendations(req: RecommendRequest):
    df = get_data()
    t_start = time.perf_counter()

    resolved = resolve_location(req.location)
    try:
        prefs = UserPreferences(
            location=resolved or req.location,
            budget=BudgetBand(req.budget),
            cuisine=req.cuisine,
            min_rating=req.min_rating,
            additional=req.additional or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    t_filter_start = time.perf_counter()
    cand_result = filter_restaurants(df, prefs)
    filter_ms = (time.perf_counter() - t_filter_start) * 1000

    candidates_df = cand_result.candidates_df
    if candidates_df.empty:
        total_ms = (time.perf_counter() - t_start) * 1000
        return RecommendResponse(
            recommendations=[],
            metrics={
                "candidate_count": 0,
                "filter_ms": filter_ms,
                "llm_ms": 0.0,
                "total_ms": total_ms,
            },
            candidate_count=0,
        )

    client = GeminiClient()
    t_llm_start = time.perf_counter()
    result = generate_recommendations(
        cand_result,
        prefs,
        client=client,
        top_n=req.top_n,
    )
    llm_ms = (time.perf_counter() - t_llm_start) * 1000
    total_ms = (time.perf_counter() - t_start) * 1000

    cand_by_id = {str(r["restaurant_id"]): r for _, r in candidates_df.iterrows()}

    cards = []
    for rec in result.recommendations:
        cand = cand_by_id.get(str(rec.restaurant_id))
        rec_name = cand["name"] if cand is not None else rec.name
        rec_cuisines = str(cand.get("cuisines", rec.cuisine)) if cand is not None else rec.cuisine
        rec_loc = str(cand.get("location", prefs.location)) if cand is not None else prefs.location
        rec_rating = float(cand.get("rating", rec.rating)) if cand is not None and pd.notna(cand.get("rating")) else rec.rating
        rec_cost = float(cand["cost_for_two"]) if cand is not None and pd.notna(cand.get("cost_for_two")) else None
        rec_url = str(cand.get("url", "")) if cand is not None else ""
        img_url = get_restaurant_image(rec_name, rec_cuisines)

        why_rec = getattr(rec, "explanation", "") or getattr(rec, "why_recommended", "")
        
        # Extract highlights
        highlights = getattr(rec, "highlights", None)
        if not highlights:
            primary_c = rec_cuisines.split(",")[0].strip() if rec_cuisines else "Top Cuisine"
            highlights = [f"★ {rec_rating:.1f} Rated", f"{prefs.budget.value.capitalize()} Band", primary_c]

        # Extract must try dishes
        must_try = getattr(rec, "must_try_dishes", None)
        if not must_try and cand is not None:
            dish_val = str(cand.get("dish_liked", "")).strip()
            if dish_val and dish_val != "nan" and dish_val != "None":
                must_try = [d.strip() for d in dish_val.split(",")[:3] if d.strip()]
            else:
                must_try = ["Chef's Special", "Signature Platter"]

        cards.append(
            RecommendationCard(
                restaurant_id=str(rec.restaurant_id),
                name=rec_name,
                cuisines=rec_cuisines,
                location=rec_loc,
                rating=rec_rating,
                cost_for_two=rec_cost,
                why_recommended=why_rec,
                highlights=highlights or [],
                must_try_dishes=must_try or [],
                url=rec_url,
                image_url=img_url,
            )
        )

    return RecommendResponse(
        recommendations=cards,
        metrics={
            "candidate_count": len(candidates_df),
            "filter_ms": filter_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms,
        },
        candidate_count=len(candidates_df),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True)
