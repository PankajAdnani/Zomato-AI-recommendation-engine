"""
Zomato Restaurant Recommendation System — Streamlit Web Application.
Authentic Zomato Design System with Gemini LLM Integration.
"""

from __future__ import annotations

import html
import json
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError

# Ensure project root is on sys.path when launched via `streamlit run`
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.store import load_restaurants
from src.filtering.engine import filter_restaurants
from src.llm.client import GeminiClient
from src.llm.recommender import generate_recommendations
from src.preferences.models import BudgetBand, UserPreferences
from src.preferences.vocab import (
    list_cuisines,
    list_locations,
    resolve_location,
    suggest_locations,
)

# Page configuration
st.set_page_config(
    page_title="Zomato | Discover Restaurants & AI Recommendations",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Specific Brand to Image Mapping for iconic Bengaluru spots
RESTAURANT_NAME_IMAGE_MAP: dict[str, str] = {
    "byg brewski": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=600&auto=format&fit=crop&q=80",  # Craft brewery & continental lounge
    "absolute barbecues": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",  # Live BBQ skewers grill
    "ab's": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",  # Live BBQ skewers grill
    "barbeque nation": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
    "flechazo": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",  # Mediterranean buffet
    "asia kitchen": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80",  # Steaming Dim sums
    "mainland china": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80",  # Chinese banquet
    "truffles": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",  # Gourmet burger & fries
    "meghana": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",  # Hyderabadi biryani
    "toit": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",  # Woodfired pizza & beer
    "vidyarthi": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80",  # Butter masala dosa
    "mtr": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80",
    "corner house": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",  # Hot chocolate fudge
    "milano": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600&auto=format&fit=crop&q=80",  # Artisanal gelato
}

# Cuisine-specific Image Mapping
CUISINE_IMAGE_MAP: dict[str, str] = {
    "brewery": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=600&auto=format&fit=crop&q=80",
    "finger food": "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&auto=format&fit=crop&q=80",
    "bbq": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
    "barbecue": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
    "biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
    "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "pasta": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=600&auto=format&fit=crop&q=80",
    "italian": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=600&auto=format&fit=crop&q=80",
    "south indian": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80",
    "dosa": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80",
    "chinese": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&auto=format&fit=crop&q=80",
    "asian": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80",
    "dim sum": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80",
    "momos": "https://images.unsplash.com/photo-1625398407797-00c14a29d119?w=600&auto=format&fit=crop&q=80",
    "north indian": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80",
    "mughlai": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
    "continental": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
    "mediterranean": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
    "european": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&auto=format&fit=crop&q=80",
    "desserts": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
    "ice cream": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600&auto=format&fit=crop&q=80",
    "bakery": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80",
    "rolls": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
    "seafood": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80",
}
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=80"


def get_restaurant_image(name: str = "", cuisines: str = "") -> str:
    """Return high-resolution culinary image matching the restaurant name or primary cuisine."""
    n_lower = name.lower()
    for brand_key, img_url in RESTAURANT_NAME_IMAGE_MAP.items():
        if brand_key in n_lower:
            return img_url

    c_lower = cuisines.lower()
    # Check individual cuisine segments (primary cuisine first)
    segments = [seg.strip() for seg in c_lower.split(",") if seg.strip()]
    for seg in segments:
        for key, img_url in CUISINE_IMAGE_MAP.items():
            if key == seg or key in seg:
                return img_url

    # Fallback substring check
    for key, img_url in CUISINE_IMAGE_MAP.items():
        if key in c_lower:
            return img_url

    return DEFAULT_IMAGE


def render_html(raw_html: str) -> None:
    """
    Render raw HTML safely into Streamlit without triggering Markdown's
    indented code block parser. Strips leading whitespace on all lines.
    """
    cleaned = "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def _load_styles() -> None:
    """Inject custom Zomato CSS design system."""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


@st.cache_data(show_spinner=False)
def _load_data() -> pd.DataFrame:
    return load_restaurants()


@st.cache_data(show_spinner=False)
def _load_vocab() -> tuple[list[str], list[str]]:
    return list_locations(), list_cuisines()


def _build_preferences(
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    additional: str,
) -> UserPreferences:
    resolved = resolve_location(location)
    return UserPreferences(
        location=resolved or location,
        budget=BudgetBand(budget),
        cuisine=cuisine,
        min_rating=min_rating,
        additional=additional or None,
    )


def render_header(active_location: str = "Bengaluru") -> str:
    """Render authentic Zomato top navigation bar with active live search input."""
    with st.container(key="zomato_navbar_container"):
        top_col1, top_col2, top_col3 = st.columns([1.1, 2.5, 1.4], vertical_alignment="center", gap="medium")
        with top_col1:
            render_html(
                """
<div class="zomato-logo-wrap">
    <span class="zomato-logo">zomato</span>
    <span class="zomato-logo-badge">AI GUIDE</span>
</div>
                """
            )
        with top_col2:
            search_query = st.text_input(
                "Search Zomato",
                placeholder=f"📍 {active_location}  |  🔍 Search for restaurant, cuisine or dish",
                label_visibility="collapsed",
                key="zomato_search_input",
            )
        with top_col3:
            render_html(
                """
<div class="nav-actions">
    <span class="nav-link-btn">Dining Out</span>
    <span class="nav-link-btn">Delivery</span>
    <span class="nav-link-btn" style="color: #E23744; font-weight: 700;">✨ Gemini AI</span>
</div>
                """
            )
    return search_query.strip() if search_query else ""


def render_search_results(query: str, results_df: pd.DataFrame) -> None:
    """Render live search results with authentic Zomato cards across the dataset."""
    total_found = len(results_df)

    render_html(
        f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #ECECEC;">
    <div>
        <div class="section-headline" style="margin-bottom: 4px; margin-top: 0;">
            🔍 Search Results for "<span style="color: #E23744;">{html.escape(query)}</span>"
        </div>
        <div style="font-size: 0.92rem; color: #696969;">
            Found <b>{total_found:,}</b> matching restaurants across Bengaluru dataset
        </div>
    </div>
</div>
        """
    )

    if results_df.empty:
        render_html(
            f"""
<div style="background: #FFFFFF; border-radius: 16px; border: 1px solid #ECECEC; padding: 48px 24px; text-align: center; margin-top: 10px;">
    <div style="font-size: 2.8rem; margin-bottom: 12px;">🍽️</div>
    <div style="font-weight: 700; font-size: 1.25rem; color: #1C1C1C; margin-bottom: 8px;">No restaurants found for "{html.escape(query)}"</div>
    <div style="font-size: 0.92rem; color: #696969; max-width: 500px; margin: 0 auto;">
        We couldn't find any spots matching your search in the Bengaluru dataset. Try searching for a cuisine like <b>Biryani</b>, <b>Pizza</b>, or <b>Chinese</b>, a locality like <b>Indiranagar</b> or <b>Koramangala</b>, or a brand like <b>Truffles</b>.
    </div>
</div>
            """
        )
        return

    # Render up to top 15 results
    display_slice = results_df.head(15)
    for _, r in display_slice.iterrows():
        rest_name = str(r["name"])
        cuisines_str = str(r.get("cuisines", ""))
        img_url = get_restaurant_image(name=rest_name, cuisines=cuisines_str)
        rating = float(r.get("rating", 4.0)) if pd.notna(r.get("rating")) else 4.0
        cost = f"₹{int(r['cost_for_two'])} for two" if pd.notna(r.get("cost_for_two")) else "Price on request"
        votes = int(r.get("votes_count", 0)) if pd.notna(r.get("votes_count")) else 0
        location = str(r.get("location", ""))
        dish_liked = str(r.get("dish_liked", "")).strip() if pd.notna(r.get("dish_liked")) and str(r.get("dish_liked", "")).strip() != "None" else ""
        url = str(r.get("url", ""))

        dish_html = ""
        if dish_liked and dish_liked.lower() != "nan":
            dish_html = f'<div style="font-size: 0.82rem; color: #1C1C1C; background: #F8F8F8; padding: 4px 10px; border-radius: 6px; margin-top: 8px; border: 1px solid #ECECEC;">🍽️ <b>Popular Dishes:</b> {html.escape(dish_liked[:110])}</div>'

        render_html(
            f"""
<div class="zomato-card" style="width: 100%; margin-bottom: 22px;">
    <div class="card-hero-image-wrap">
        <img class="card-hero-img" src="{img_url}" alt="{html.escape(rest_name)}"/>
        <div class="card-top-badges">
            <span class="promoted-pill">MATCHED RESULT</span>
            <span class="rank-pill">📍 {html.escape(location)}</span>
        </div>
    </div>
    <div class="card-body">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;">
            <div style="flex: 1;">
                <h3 class="restaurant-name">{html.escape(rest_name)}</h3>
                <div class="card-cuisine" style="font-size: 0.95rem; margin-top: 4px; color: #4F4F4F;">{html.escape(cuisines_str)}</div>
                <div style="font-size: 0.88rem; color: #828282; margin-top: 6px;">
                    📍 {html.escape(location)} • {votes:,} customer reviews on Zomato
                </div>
                {dish_html}
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px; min-width: 160px;">
                <div class="zomato-rating" style="font-size: 1.05rem; padding: 4px 12px;">★ {rating:.1f}</div>
                <div class="card-cost" style="font-size: 0.95rem; font-weight: 700;">{cost}</div>
            </div>
        </div>
        <div class="card-footer-row" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #F0F0F0; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; gap: 8px;">
                <span class="tag-badge">🛵 Online Order Available</span>
                <span class="tag-badge">🪑 Dine-in</span>
            </div>
            <a href="{url}" target="_blank" class="zomato-btn-primary" style="padding: 8px 22px; font-size: 0.9rem;">View on Zomato ↗</a>
        </div>
    </div>
</div>
            """
        )

    if total_found > 15:
        render_html(
            f"""
<div style="text-align: center; color: #828282; font-size: 0.88rem; padding: 14px; background: #FAFAFA; border-radius: 10px; border: 1px dashed #DCDCDC;">
    Showing top 15 of {total_found:,} matching restaurants. Type a more specific cuisine or locality to narrow down.
</div>
            """
        )


def render_category_tabs() -> None:
    """Render authentic service category switch tabs."""
    render_html(
        """
<div class="zomato-tab-bar">
    <div class="zomato-tab-item active">
        <div class="tab-icon-wrap">🍽️</div>
        <span>Dining Out</span>
    </div>
    <div class="zomato-tab-item">
        <div class="tab-icon-wrap">🛵</div>
        <span>Delivery</span>
    </div>
    <div class="zomato-tab-item">
        <div class="tab-icon-wrap">🍸</div>
        <span>Nightlife</span>
    </div>
</div>
        """
    )


def render_hero_banner(total_restaurants: int, total_localities: int) -> None:
    """Render 'Better food for more people' banner with authentic floating stats."""
    render_html(
        f"""
<div class="hero-banner-container">
    <div class="hero-title">Better food for more people</div>
    <div class="hero-subtitle">
        Discover exceptional dining across Bengaluru tailored precisely to your budget,
        taste, and mood — powered by Gemini AI and real Zomato customer reviews.
    </div>
    <div class="stats-pill-container">
        <div class="stat-item">
            <div class="stat-value">
                <span>{total_restaurants:,}+</span>
                <span class="stat-icon">🏬</span>
            </div>
            <div class="stat-label">Restaurants in Bengaluru</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">
                <span>{total_localities:,}+</span>
                <span class="stat-icon">📍</span>
            </div>
            <div class="stat-label">Localities Covered</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">
                <span>Gemini 3.5</span>
                <span class="stat-icon">✨</span>
            </div>
            <div class="stat-label">AI Recommendation Engine</div>
        </div>
    </div>
</div>
        """
    )


def render_inspiration_grid() -> None:
    """Render circular dish inspiration carousel with large, clear, equal-sized images."""
    dishes = [
        ("Biryani", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300&auto=format&fit=crop&q=80"),
        ("Pizza", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300&auto=format&fit=crop&q=80"),
        ("North Indian", "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=300&auto=format&fit=crop&q=80"),
        ("Burger", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300&auto=format&fit=crop&q=80"),
        ("South Indian", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=300&auto=format&fit=crop&q=80"),
        ("Chinese", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=300&auto=format&fit=crop&q=80"),
        ("Italian", "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=300&auto=format&fit=crop&q=80"),
        ("Desserts", "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=300&auto=format&fit=crop&q=80"),
    ]
    render_html('<div class="section-headline">Inspiration for your next meal</div>')
    items_html = "".join(
        f'<div class="cuisine-item"><img class="cuisine-circle-img" src="{img}" alt="{name}"/><span class="cuisine-label">{name}</span></div>'
        for name, img in dishes
    )
    render_html(f'<div class="cuisine-grid">{items_html}</div>')


def render_top_brands() -> None:
    """Render authentic top brands row from Bengaluru dataset without code block formatting."""
    brands = [
        ("Meghana Foods", "🍛", "30–35 min"),
        ("Empire Restaurant", "🍗", "25–30 min"),
        ("Truffles", "🍔", "35–40 min"),
        ("Beijing Bites", "🍜", "30–35 min"),
        ("Nandhana Palace", "🍲", "40–45 min"),
        ("Corner House", "🍨", "20–25 min"),
    ]
    render_html('<div class="section-headline">Top brands for you in Bengaluru</div>')
    brands_html = "".join(
        f'<div class="brand-item"><div class="brand-avatar">{icon}</div><div class="brand-name">{name}</div><div class="brand-time">{timing}</div></div>'
        for name, icon, timing in brands
    )
    render_html(f'<div class="brand-grid">{brands_html}</div>')


def render_feature_cards() -> None:
    """Render 'What's waiting for you on the app' feature badges without code blocks."""
    render_html('<div class="section-headline">What’s waiting for you</div>')
    features = [
        ("Healthy & Diet", "🥗"),
        ("Pure Veg Mode", "🟢"),
        ("Gourmet Fine Dine", "🍷"),
        ("Pocket Friendly", "🏷️"),
        ("Gemini AI Guide", "🤖"),
        ("Table Booking", "🪑"),
    ]
    feats_html = "".join(
        f'<div class="feature-card"><span class="feature-icon">{icon}</span><span class="feature-title">{title}</span></div>'
        for title, icon in features
    )
    render_html(f'<div class="feature-cards-grid">{feats_html}</div>')


def main() -> None:
    _load_styles()

    try:
        df = _load_data()
        locations, cuisines = _load_vocab()
    except FileNotFoundError as exc:
        st.error(f"Data loading error: {exc}")
        st.stop()

    llm_client = GeminiClient()
    is_llm_ready = llm_client.is_available()

    # Sidebar Engine Details & Diagnostics
    with st.sidebar:
        st.markdown(
            """
<div class="sidebar-info-card">
    <div style="font-weight: 700; font-size: 1.05rem; color: #1C1C1C; margin-bottom: 8px;">⚙️ Engine Status</div>
    <div style="color: #24963F; font-weight: 700; margin-bottom: 4px;">🟢 Gemini AI Active</div>
    <div style="font-size: 0.85rem; color: #696969;">Model: <b>gemini-3.5-flash-lite</b></div>
    <div style="font-size: 0.85rem; color: #696969;">Tier: <b>Free / Standard</b></div>
</div>
<div class="sidebar-info-card">
    <div style="font-weight: 700; font-size: 1.05rem; color: #1C1C1C; margin-bottom: 8px;">📊 Zomato Dataset</div>
    <div style="font-size: 0.88rem; color: #374151; margin-bottom: 3px;">Restaurants: <b>{:,}</b></div>
    <div style="font-size: 0.88rem; color: #374151; margin-bottom: 3px;">Localities: <b>{:,}</b></div>
    <div style="font-size: 0.88rem; color: #374151;">Cuisines: <b>{:,}</b></div>
</div>
            """.format(len(df), len(locations), len(cuisines)),
            unsafe_allow_html=True,
        )

    # Render Top Navigation Bar with active live search
    search_query = render_header(active_location="Bengaluru")

    # Render Service Category Switcher Tabs
    render_category_tabs()

    # Main Grid Layout: Form on the Left (1.7), Content on the Right (2.3)
    col_form, col_results = st.columns([1.7, 2.3], gap="medium")

    with col_form:
        render_html(
            """
<div class="find-spot-banner">
    <div class="find-spot-title">
        🎯 Find Your Perfect Spot
    </div>
    <div class="find-spot-subtitle">
        Select your location, budget, and cuisine preferences and let Gemini AI curate the best restaurants for you.
    </div>
</div>
            """
        )

        with st.form("preferences_form"):
            location = st.selectbox(
                "📍 Select Location / Locality",
                options=locations,
                index=locations.index("Koramangala 5th Block")
                if "Koramangala 5th Block" in locations
                else 0,
            )
            custom_location = st.text_input(
                "Or custom area (optional override)",
                placeholder="e.g. Indiranagar, HSR, Whitefield",
            )
            budget = st.selectbox(
                "💰 Budget Band",
                options=[b.value for b in BudgetBand],
                format_func=lambda v: f"{v.capitalize()} (< ₹500 for two)"
                if v == "low"
                else (f"{v.capitalize()} (₹500–1500 for two)" if v == "medium" else f"{v.capitalize()} (> ₹1500 for two)"),
                index=1,
            )
            cuisine = st.selectbox(
                "🍕 Preferred Cuisine",
                options=cuisines,
                index=cuisines.index("North Indian") if "North Indian" in cuisines else 0,
            )
            min_rating = st.slider(
                "⭐ Minimum Rating Threshold",
                min_value=0.0,
                max_value=5.0,
                value=3.8,
                step=0.1,
            )
            additional = st.text_area(
                "📝 Special Preferences / Mood (Optional)",
                placeholder="e.g. romantic candle light dinner, rooftop view, family-friendly with kids",
                max_chars=500,
                height=135,
            )
            top_n = st.slider(
                "🔢 Number of Recommendations",
                min_value=1,
                max_value=10,
                value=4,
            )

            submitted = st.form_submit_button("✨ Discover Recommendations", type="primary")

    with col_results:
        if not submitted:
            if search_query:
                # Active Search Mode: filter across all 9,249+ restaurants
                search_str = search_query.lower()
                mask = (
                    df["name"].astype(str).str.lower().str.contains(search_str, regex=False, na=False)
                    | df["cuisines"].astype(str).str.lower().str.contains(search_str, regex=False, na=False)
                    | df["location"].astype(str).str.lower().str.contains(search_str, regex=False, na=False)
                    | df["dish_liked"].astype(str).str.lower().str.contains(search_str, regex=False, na=False)
                )
                search_results = df[mask].sort_values(by=["rating", "votes_count"], ascending=[False, False])
                render_search_results(search_query, search_results)
                return

            # Landing Screen: Render authentic Zomato showcases!
            render_hero_banner(len(df), len(locations))
            render_inspiration_grid()
            render_top_brands()
            render_feature_cards()

            # Trending Restaurants Showcase with 3 distinct cuisine-accurate legendary spots
            render_html('<div class="section-headline">🔥 Trending & Top-Rated in Bengaluru</div>')

            # Curate 3 distinct top-rated Bengaluru culinary legends representing different cuisines:
            # 1. Byg Brewski (Brewery, Continental & Finger Food)
            # 2. AB's - Absolute Barbecues (Live BBQ Skewers & Mediterranean Buffet)
            # 3. Asia Kitchen by Mainland China (Authentic Chinese, Dim Sums & Asian)
            trending_candidates = []
            for target_name in ["Byg Brewski", "Absolute Barbecues", "Asia Kitchen"]:
                match = df[df["name"].str.contains(target_name, case=False, na=False)]
                if not match.empty:
                    trending_candidates.append(match.iloc[0])

            # Fallback if specific names not found
            if len(trending_candidates) < 3:
                top_slice = df.sort_values(by=["rating", "votes_count"], ascending=[False, False]).head(3)
                trending_candidates = [r for _, r in top_slice.iterrows()]

            for r in trending_candidates:
                rest_name = str(r["name"])
                cuisines_str = str(r.get("cuisines", ""))
                img_url = get_restaurant_image(name=rest_name, cuisines=cuisines_str)
                rating = float(r.get("rating", 4.0))
                cost = f"₹{int(r['cost_for_two'])} for two" if pd.notna(r.get("cost_for_two")) else "Price on request"
                url = str(r.get("url", ""))

                render_html(
                    f"""
<div class="zomato-card" style="width: 100%; margin-bottom: 22px;">
    <div class="card-hero-image-wrap">
        <img class="card-hero-img" src="{img_url}" alt="{html.escape(rest_name)}"/>
        <div class="card-top-badges">
            <span class="promoted-pill">POPULAR SPOT</span>
            <span class="rank-pill">⭐ BENGALURU LEGEND</span>
        </div>
    </div>
    <div class="card-body">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 24px;">
            <div style="flex: 1;">
                <h3 class="restaurant-name">{html.escape(rest_name)}</h3>
                <div class="card-cuisine" style="font-size: 0.95rem; margin-top: 4px; color: #4F4F4F;">{html.escape(cuisines_str)}</div>
                <div style="font-size: 0.88rem; color: #828282; margin-top: 6px;">
                    📍 {html.escape(str(r['location']))} • {int(r.get('votes_count', 0)):,} customer reviews on Zomato
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px; min-width: 170px;">
                <div class="zomato-rating" style="font-size: 1.05rem; padding: 4px 12px;">★ {rating:.1f}</div>
                <div class="card-cost" style="font-size: 0.95rem; font-weight: 700;">{cost}</div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #E23744; background: #FFF0F1; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(226,55,68,0.2);">
                    🏆 Top 1% in Bengaluru
                </div>
            </div>
        </div>
        <div class="card-footer-row" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #F0F0F0; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; gap: 8px;">
                <span class="tag-badge">🛵 Online Order Available</span>
                <span class="tag-badge">🪑 Table Booking</span>
                <span class="tag-badge">🥘 Dine-in Available</span>
            </div>
            <a href="{url}" target="_blank" class="zomato-btn-primary" style="padding: 8px 22px; font-size: 0.9rem;">View on Zomato ↗</a>
        </div>
    </div>
</div>
                    """
                )
            return

        # =====================================================================
        # Submitted Flow: Filter & Execute LLM Recommendations
        # =====================================================================
        chosen_location = custom_location.strip() or location
        suggestions = suggest_locations(chosen_location) if custom_location.strip() else []

        try:
            prefs = _build_preferences(
                location=chosen_location,
                budget=budget,
                cuisine=cuisine,
                min_rating=min_rating,
                additional=additional,
            )
        except (ValidationError, ValueError) as exc:
            st.error("Invalid input preferences.")
            if isinstance(exc, ValidationError):
                for err in exc.errors():
                    field_name = ".".join(str(p) for p in err.get("loc", ()))
                    st.write(f"- **{field_name or 'input'}**: {err.get('msg')}")
            else:
                st.write(str(exc))
            if suggestions:
                st.warning("Did you mean: " + ", ".join(suggestions))
            return

        # Active Filter Chips Row
        render_html(
            f"""
<div style="margin-bottom: 14px;">
    <span class="filter-chip">📍 <b>{html.escape(prefs.location)}</b></span>
    <span class="filter-chip">💰 <b>{html.escape(prefs.budget.value.capitalize())}</b></span>
    <span class="filter-chip">🍕 <b>{html.escape(prefs.cuisine)}</b></span>
    <span class="filter-chip">⭐ <b>≥ {prefs.min_rating}</b></span>
</div>
            """
        )

        # Filtering Execution
        t0 = time.perf_counter()
        with st.spinner("Filtering candidates across Zomato Bengaluru dataset..."):
            candidate_result = filter_restaurants(df, prefs, top_k=25, allow_relaxation=True)
        t_filter = (time.perf_counter() - t0) * 1000

        if candidate_result.candidates_df.empty:
            st.error("No matching restaurants found in the dataset for these criteria.")
            return

        # Progressive relaxation notice
        if candidate_result.relaxation_notes:
            for note in candidate_result.relaxation_notes:
                st.warning(f"⚠️ **Progressive Relaxation Active**: {note}")

        # Gemini LLM Recommendation Execution
        t1 = time.perf_counter()
        with st.spinner("Gemini AI is analyzing reviews and crafting custom recommendations..."):
            rec_response = generate_recommendations(
                candidate_result, prefs, top_n=top_n, client=llm_client
            )
        t_llm = (time.perf_counter() - t1) * 1000
        t_total = t_filter + t_llm

        # Latency & Candidate Performance Metrics Dashboard
        render_html(
            f"""
<div class="metrics-dashboard-grid">
    <div class="metric-box">
        <div class="metric-box-label">🔍 Candidates Scanned</div>
        <div class="metric-box-val">
            <span class="metric-number">{candidate_result.total_matched:,}</span>
            <span class="metric-unit">Restaurants</span>
        </div>
        <div class="metric-box-sub">Matched from Zomato dataset</div>
    </div>
    <div class="metric-box">
        <div class="metric-box-label">⚡ Filter Time</div>
        <div class="metric-box-val">
            <span class="metric-number">{t_filter:.0f}</span>
            <span class="metric-unit">ms (Milliseconds)</span>
        </div>
        <div class="metric-box-sub">Multi-criteria search speed</div>
    </div>
    <div class="metric-box">
        <div class="metric-box-label">🤖 Gemini LLM Time</div>
        <div class="metric-box-val">
            <span class="metric-number">{t_llm:.0f}</span>
            <span class="metric-unit">ms ({t_llm / 1000:.2f} s)</span>
        </div>
        <div class="metric-box-sub">AI ranking & reasoning</div>
    </div>
    <div class="metric-box">
        <div class="metric-box-label">⏱️ Total Latency</div>
        <div class="metric-box-val">
            <span class="metric-number">{t_total / 1000:.2f}</span>
            <span class="metric-unit">Seconds ({t_total:.0f} ms)</span>
        </div>
        <div class="metric-box-sub">End-to-end response time</div>
    </div>
</div>
            """
        )

        # Gemini AI Summary Card
        render_html(
            f"""
<div class="ai-summary-card">
    <div class="ai-summary-header">
        <span>✨</span>
        <span>AI Curated Guide • {rec_response.provider.capitalize()} ({rec_response.model})</span>
    </div>
    <div class="ai-summary-text">{html.escape(rec_response.summary)}</div>
</div>
            """
        )

        render_html(
            f'<div class="section-headline">Top {len(rec_response.recommendations)} Recommended Restaurants</div>'
        )

        # Build candidate metadata map
        cand_map = {}
        if not candidate_result.candidates_df.empty:
            for _, r in candidate_result.candidates_df.iterrows():
                cand_map[str(r.get("restaurant_id", ""))] = r.to_dict()
                cand_map[str(r.get("name", "")).lower()] = r.to_dict()

        rec_cards_html = []
        for item in rec_response.recommendations:
            r_meta = cand_map.get(item.restaurant_id) or cand_map.get(item.name.lower(), {})
            url = r_meta.get("url") or f"https://www.zomato.com/bangalore?q={html.escape(item.name)}"
            online_order = str(r_meta.get("online_order", "")).lower() == "yes"
            book_table = str(r_meta.get("book_table", "")).lower() == "yes"
            img_url = get_restaurant_image(name=item.name, cuisines=item.cuisine)
            location_name = str(r_meta.get("location", prefs.location))

            tag_html = ""
            if online_order:
                tag_html += '<span class="tag-badge">🛵 Online Order Available</span>'
            if book_table:
                tag_html += '<span class="tag-badge">🪑 Book Table</span>'
            if not tag_html:
                tag_html += '<span class="tag-badge">🥘 Dine-in Available</span>'

            card = f"""
<div class="rec-card-square">
    <div class="card-hero-image-wrap">
        <img class="card-hero-img" src="{img_url}" alt="{html.escape(item.name)}"/>
        <div class="card-top-badges">
            <span class="promoted-pill">TOP MATCH</span>
            <span class="rank-pill">#{item.rank} RECOMMENDATION</span>
        </div>
    </div>
    <div class="card-body">
        <div class="card-header-row">
            <h3 class="restaurant-name">{html.escape(item.name)}</h3>
            <div class="zomato-rating">★ {item.rating:.1f}</div>
        </div>
        <div class="card-sub-row">
            <span class="card-cuisine">{html.escape(item.cuisine)}</span>
            <span class="card-cost">{html.escape(item.estimated_cost)}</span>
        </div>
        <div style="font-size: 0.85rem; color: #828282; margin-bottom: 8px;">
            📍 {html.escape(location_name)}
        </div>
        <div class="ai-explanation-box">
            <div class="ai-explanation-title">
                <span>✨</span>
                <span>Why this fits your choice</span>
            </div>
            <div>{html.escape(item.explanation)}</div>
        </div>
        <div class="card-footer-row">
            <div>{tag_html}</div>
            <a href="{url}" target="_blank" class="zomato-btn-primary">View on Zomato ↗</a>
        </div>
    </div>
</div>
"""
            rec_cards_html.append(card)

        render_html(f'<div class="recommendations-grid">{"".join(rec_cards_html)}</div>')

        # Diagnostics & JSON Context for developer verification
        with st.expander("🛠️ Developer Diagnostics & LLM Payload"):
            tab1, tab2 = st.tabs(["Candidate Set Table", "Gemini Response JSON"])
            with tab1:
                st.dataframe(
                    candidate_result.candidates_df[
                        ["restaurant_id", "name", "location", "cuisines", "rating", "votes_count", "cost_for_two", "score"]
                    ],
                    use_container_width=True,
                )
            with tab2:
                st.json(rec_response.model_dump())


if __name__ == "__main__":
    main()
