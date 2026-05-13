from fastapi.testclient import TestClient


def test_analyze_line_basic(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-line", json={"line": "I see the fire in your eyes"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["normalized_line"] == "i see the fire in your eyes"
    # "I see the fire in your eyes" ~ 8 syllables; allow a small band.
    assert 7 <= body["total_syllables"] <= 9
    assert body["last_word"]["normalized"] == "eyes"
    assert body["last_word"]["pronunciation_found"] is True
    assert len(body["tokens"]) == 7


def test_analyze_line_strips_punctuation_tokens(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-line", json={"line": "Hello, world!"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [t["normalized"] for t in body["tokens"]] == ["hello", "world"]
    assert body["last_word"]["normalized"] == "world"


def test_analyze_line_blank_input_is_validation_error(client: TestClient) -> None:
    resp = client.post("/v1/analyze-line", json={"line": "   "})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_analyze_line_unknown_word_has_count(client: TestClient) -> None:
    resp = client.post("/v1/analyze-line", json={"line": "qzqzqz"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_syllables"] >= 1
    assert body["tokens"][0]["pronunciation_found"] is False
