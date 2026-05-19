from fastapi.testclient import TestClient


def test_spanish_line_basic(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-line",
        json={"line": "yo te quiero más que ayer", "language": "es"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "es"
    # yo (1) te (1) quie-ro (2) más (1) que (1) a-yer (2) ≈ 8 syllables.
    assert 7 <= body["total_syllables"] <= 9
    assert body["last_word"]["normalized"] == "ayer"


def test_spanish_accented_word_counted_correctly(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-line",
        json={"line": "corazón", "language": "es"},
    )
    body = resp.json()
    assert body["tokens"][0]["syllables"] == 3


def test_spanish_preserves_n_tilde(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-line",
        json={"line": "mañana es otro día", "language": "es"},
    )
    body = resp.json()
    normalized = [t["normalized"] for t in body["tokens"]]
    assert "mañana" in normalized
    assert "día" in normalized
