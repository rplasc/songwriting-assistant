from fastapi.testclient import TestClient


def test_rhymes_known_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["normalized_word"] == "fire"
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    assert all(r["word"] != "fire" for r in body["rhymes"])
    assert body["meta"] == {"limit": 10, "mode": "perfect", "include_near": False}
    assert all(r["rhyme_type"] == "perfect" for r in body["rhymes"])
    assert all(0.0 <= r["score"] <= 1.0 for r in body["rhymes"])
    # Without include_metadata, match_reason should be omitted/null.
    assert all(r["match_reason"] is None for r in body["rhymes"])


def test_rhymes_unknown_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "qzqzqz"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pronunciations_found"] is False
    assert body["rhymes"] == []


def test_rhymes_blank_word_is_validation_error(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "  "})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"


def test_rhymes_limit_is_clamped(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 9999})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["limit"] == 25
    assert len(body["rhymes"]) <= 25


def test_rhymes_rejects_multi_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "two words"})
    assert resp.status_code == 422


def test_rhymes_near_mode_returns_near_type(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "cat", "mode": "near", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["mode"] == "near"
    assert body["meta"]["include_near"] is True
    assert all(r["rhyme_type"] == "near" for r in body["rhymes"])
    # Perfect rhymes (e.g. "hat", "bat") should not show up inside the near bucket.
    near_words = {r["word"] for r in body["rhymes"]}
    assert "hat" not in near_words
    assert "bat" not in near_words


def test_rhymes_near_and_perfect_are_disjoint(client: TestClient) -> None:
    perfect = client.post("/v1/rhymes", json={"word": "fire", "limit": 25}).json()
    near = client.post(
        "/v1/rhymes", json={"word": "fire", "mode": "near", "limit": 25}
    ).json()
    perfect_words = {r["word"] for r in perfect["rhymes"]}
    near_words = {r["word"] for r in near["rhymes"]}
    assert perfect_words.isdisjoint(near_words)


def test_rhymes_include_near_flag_is_legacy_alias(client: TestClient) -> None:
    """Phase 1 clients that set `include_near: true` should now get near rhymes."""
    resp = client.post("/v1/rhymes", json={"word": "cat", "include_near": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["mode"] == "near"


def test_rhymes_include_metadata_adds_match_reason(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "fire", "limit": 5, "include_metadata": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(r["match_reason"] for r in body["rhymes"])


def test_rhymes_inflection_does_not_top_results(client: TestClient) -> None:
    """An inflected form of the query (`runs` for `run`) should not lead the list."""
    resp = client.post("/v1/rhymes", json={"word": "run", "limit": 10})
    body = resp.json()
    words = [r["word"] for r in body["rhymes"]]
    if "runs" in words:
        assert words.index("runs") > 0
