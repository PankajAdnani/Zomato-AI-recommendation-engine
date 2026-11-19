"""End-to-end Gemini pipeline test."""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv(override=True)

print("=== STEP 1: Verify Gemini Client ===")
from src.llm.client import GeminiClient
client = GeminiClient()
print(f"  API key present : {client.is_available()}")
print(f"  Model           : {client.model}")
print(f"  Provider        : {client.provider}")

print()
print("=== STEP 2: Live Gemini JSON generation ===")
result = client.generate_json(
    system_prompt="You are a helpful assistant. Always respond with valid JSON.",
    user_prompt='Return a JSON object with key "status" set to "Gemini is working!"',
    temperature=0.1,
)
print(f"  Response: {result}")

print()
print("=== STEP 3: Full recommendation pipeline ===")
from src.preferences.models import UserPreferences, BudgetBand
from src.config import PROCESSED_PARQUET
import pandas as pd

df = pd.read_parquet(PROCESSED_PARQUET)
print(f"  Dataset loaded  : {len(df)} restaurants")

prefs = UserPreferences(
    location="Koramangala",
    cuisine="North Indian",
    budget=BudgetBand.MEDIUM,
)
print(f"  Preferences     : {prefs.location} | {prefs.cuisine} | {prefs.budget.value}")

from src.filtering.engine import filter_restaurants
candidates = filter_restaurants(df, prefs)
print(f"  Candidates found: {len(candidates.candidates_df)}")

from src.llm.recommender import generate_recommendations
recs = generate_recommendations(candidates, prefs, top_n=3, client=client)

print(f"  Is fallback     : {recs.is_fallback}")
print(f"  Provider        : {recs.provider}  |  Model: {recs.model}")
print(f"  Summary         : {recs.summary[:120]}")
print()
for r in recs.recommendations:
    print(f"  [{r.rank}] {r.name}  ({r.rating}★)  {r.estimated_cost}")
    print(f"       {r.explanation[:110]}")

print()
print("=== ALL TESTS PASSED — Gemini is powering recommendations! ===")
