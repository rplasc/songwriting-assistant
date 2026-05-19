"""Pin a handful of well-known English rhyme behaviors so the LanguageEngine
refactor does not silently drift Phase 2 results."""

from fastapi.testclient import TestClient


def test_fire_top_results_include_known_perfect_rhymes(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 25})
    body = resp.json()
    words = {r["word"] for r in body["rhymes"]}
    # Stable phase-2 perfect rhymes for "fire" — all of these are in CMU
    # with frequencies well above the corpus floor.
    expected = {"desire", "tire", "wire", "hire", "higher"}
    overlap = words & expected
    assert len(overlap) >= 3, f"only {sorted(overlap)} of {expected} surfaced"


def test_cat_perfect_top_is_perfect(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "cat", "limit": 5})
    body = resp.json()
    assert body["rhymes"][0]["rhyme_type"] == "perfect"


def test_wonderful_uses_family_tier(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "wonderful", "limit": 20})
    body = resp.json()
    types = {r["rhyme_type"] for r in body["rhymes"]}
    assert "family" in types
    assert types.issubset({"perfect", "family", "near"})


def test_love_returns_some_results(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "love", "limit": 10})
    body = resp.json()
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0


def test_heuristic_fallback_still_works(client: TestClient) -> None:
    """The English-only spelling heuristic must still fire for unknown words."""
    resp = client.post("/v1/rhymes", json={"word": "wundurful", "limit": 10})
    body = resp.json()
    assert body["pronunciations_found"] is True
    assert all(r["rhyme_type"] == "family" for r in body["rhymes"])
