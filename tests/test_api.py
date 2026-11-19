"""Unit tests for FastAPI backend server endpoints."""

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["restaurants_count"] > 9000
    assert data["localities_count"] > 50


def test_metadata_endpoint():
    resp = client.get("/api/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "locations" in data
    assert "cuisines" in data
    assert "budget_bands" in data
    assert len(data["locations"]) > 50
    assert len(data["cuisines"]) > 10


def test_trending_endpoint():
    resp = client.get("/api/trending")
    assert resp.status_code == 200
    data = resp.json()
    assert "trending" in data
    assert len(data["trending"]) >= 3


def test_search_endpoint():
    resp = client.get("/api/search?q=truffles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] > 0
    assert len(data["results"]) > 0
    assert any("truffles" in r["name"].lower() for r in data["results"])


def test_recommend_endpoint():
    payload = {
        "location": "Koramangala 5th Block",
        "budget": "medium",
        "cuisine": "North Indian",
        "min_rating": 3.8,
        "additional": "cozy ambiance",
        "top_n": 2,
    }
    resp = client.post("/api/recommend", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert "metrics" in data
    assert data["candidate_count"] > 0
    assert len(data["recommendations"]) > 0
