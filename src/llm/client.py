"""Gemini LLM API client wrapper using the official google-genai SDK."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.config import get_gemini_api_key, get_gemini_model, get_llm_provider

logger = logging.getLogger(__name__)

# Gemini models to try in order if primary fails (updated Nov 2026)
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]


class GeminiClient:
    """Client for Google Gemini LLM API interaction using the google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else get_gemini_api_key()
        self.model = model or get_gemini_model() or "gemini-3.5-flash-lite"
        self.provider = get_llm_provider() or "gemini"
        self._client: Any = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model: {self.model}")
            except Exception as exc:
                logger.warning(f"Failed to initialize Gemini client: {exc}")

    def is_available(self) -> bool:
        """Check if Gemini API client is properly configured with an API key."""
        if self.api_key is None:
            self.api_key = get_gemini_api_key()
            if self.api_key:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=self.api_key)
                except Exception as exc:
                    logger.warning(f"Failed to initialize Gemini client: {exc}")

        return bool(self.api_key and self.api_key.strip() and self._client is not None)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Send a generation request to Gemini and return a JSON string.

        Tries the configured model first, then falls back through FALLBACK_MODELS
        if a model is not found or unavailable.
        """
        if not self.is_available() or self._client is None:
            raise RuntimeError(
                "Gemini API key is not configured. "
                "Please add GEMINI_API_KEY to your .env file."
            )

        from google import genai
        from google.genai import types

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        candidate_models = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]
        last_exception: Exception | None = None

        for target_model in candidate_models:
            try:
                response = self._client.models.generate_content(
                    model=target_model,
                    contents=combined_prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=2000,
                        response_mime_type="application/json",
                    ),
                )

                content = response.text
                if not content:
                    raise ValueError("Gemini API returned an empty response.")

                # Validate it's parseable JSON before returning
                json.loads(content)

                self.model = target_model  # Track the working model
                logger.info(f"Gemini response received from model: {target_model}")
                return content.strip()

            except Exception as exc:
                err_str = str(exc).lower()
                last_exception = exc
                # Model not found, deprecated, 503 high demand, 429 rate limit -> try next
                if any(kw in err_str for kw in ["404", "not found", "no longer available", "deprecated", "invalid", "503", "unavailable", "demand", "429", "resource_exhausted", "quota"]):
                    logger.warning(f"Model '{target_model}' unavailable: {exc}. Trying fallback...")
                    continue
                else:
                    logger.error(f"Gemini API error ({target_model}): {exc}")
                    continue

        raise RuntimeError(
            f"All Gemini models failed. Last error: {last_exception}"
        )


# ---------------------------------------------------------------------------
# Backward-compatibility alias so existing imports still work
# (recommender.py imports GroqClient — alias it to GeminiClient)
# ---------------------------------------------------------------------------
GroqClient = GeminiClient
