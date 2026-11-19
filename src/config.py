"""Project configuration and environment loader."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def reload_env() -> None:
    """Reload environment variables from root and src .env files."""
    root_env = PROJECT_ROOT / ".env"
    src_env = PROJECT_ROOT / "src" / ".env"

    if root_env.exists():
        load_dotenv(root_env, override=True)
    if src_env.exists():
        load_dotenv(src_env, override=True)
    load_dotenv(override=True)


# Initial load
reload_env()

HF_DATASET_ID = os.getenv(
    "HF_DATASET_ID",
    "ManikaSaini/zomato-restaurant-recommendation",
)

DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", str(PROJECT_ROOT / "data" / "raw")))
DATA_PROCESSED_DIR = Path(
    os.getenv("DATA_PROCESSED_DIR", str(PROJECT_ROOT / "data" / "processed"))
)

PROCESSED_PARQUET = DATA_PROCESSED_DIR / "restaurants.parquet"
PROCESSED_CSV = DATA_PROCESSED_DIR / "restaurants.csv"
DATA_DICTIONARY_PATH = DATA_PROCESSED_DIR / "data_dictionary.json"

# Budget bands based on approx cost for two (INR in this dataset)
BUDGET_LOW_MAX = int(os.getenv("BUDGET_LOW_MAX", "499"))
BUDGET_MEDIUM_MAX = int(os.getenv("BUDGET_MEDIUM_MAX", "1500"))


# ---------------------------------------------------------------------------
# Gemini (Primary LLM)
# ---------------------------------------------------------------------------

def get_gemini_api_key() -> str:
    """Dynamically get GEMINI_API_KEY from environment, reloading .env if needed."""
    reload_env()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key


def get_gemini_model() -> str:
    """Dynamically get GEMINI_MODEL from environment."""
    reload_env()
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()


# ---------------------------------------------------------------------------
# Groq (Legacy / fallback reference — models no longer available on free tier)
# ---------------------------------------------------------------------------

def get_groq_api_key() -> str:
    """Dynamically get GROQ_API_KEY from environment, reloading .env if needed."""
    reload_env()
    key = os.getenv("GROQ_API_KEY", "").strip()
    return key


def get_groq_model() -> str:
    """Dynamically get GROQ_MODEL from environment."""
    reload_env()
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


def get_llm_provider() -> str:
    """Dynamically get LLM_PROVIDER from environment."""
    reload_env()
    return os.getenv("LLM_PROVIDER", "gemini").strip()


# ---------------------------------------------------------------------------
# Convenience module-level accessors
# ---------------------------------------------------------------------------
GEMINI_API_KEY = get_gemini_api_key()
GEMINI_MODEL = get_gemini_model()
GROQ_API_KEY = get_groq_api_key()
GROQ_MODEL = get_groq_model()
LLM_PROVIDER = get_llm_provider()
