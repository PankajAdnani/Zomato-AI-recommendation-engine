# Phase 4 — Recommendation Engine (LLM)

> Status: **Implemented**  
> Parent: [architecture.md](../architecture.md)  
> Depends on: [Phase 2](phase-2-user-input.md), [Phase 3](phase-3-filtering.md)  
> Provider: Groq (`llama-3.3-70b-versatile`) with heuristic fallback

## Objectives

Use an LLM to **rank** candidates, **explain** fit, and optionally **summarize** choices.

## Architecture

```
Candidates + Preferences → Prompt Builder → Groq Client → Parser/Validator → RankedRecommendations
```

## Prompt Principles

1. Grounding — only recommend from candidate list
2. Explicit ranking criteria (location, budget, cuisine, rating, additional)
3. Short, specific explanations
4. Strict JSON / structured output
5. Treat `additional` as untrusted user text

## Output Schema

```json
{
  "summary": "One short paragraph overview",
  "recommendations": [
    {
      "restaurant_id": "123",
      "rank": 1,
      "name": "Example Bistro",
      "cuisine": "Italian",
      "rating": 4.5,
      "estimated_cost": "₹800 for two",
      "explanation": "Matches Italian cuisine within medium budget..."
    }
  ]
}
```

## Implemented Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Models | `src/llm/models.py` | Pydantic response schemas |
| Prompts | `src/llm/prompts.py` | System & User templates |
| Client | `src/llm/client.py` | Groq SDK client wrapper |
| Recommender | `src/llm/recommender.py` | Orchestration, anti-hallucination, heuristic fallback |

## Reliability & Safety

- Hallucination safeguard drops IDs not present in candidate set
- Graceful heuristic fallback when `GROQ_API_KEY` is missing or API fails
- Environment API key configuration (`.env`, git-ignored)

## Exit Criteria

- [x] Top-N with explanations
- [x] Hallucinated IDs rejected
- [x] Fallback works without LLM

## Change Log

| Date | Change |
|------|--------|
| 2026-10-08 | Doc split from architecture.md |
| 2026-10-10 | Implemented Groq client, anti-hallucination, fallback recommender, unit tests, and UI integration |

