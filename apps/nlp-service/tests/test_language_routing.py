from fastapi.testclient import TestClient


def test_unsupported_language_returns_422(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "language": "fr"})
    # Fails Pydantic Literal validation first → validation_error.
    assert resp.status_code == 422


def test_default_language_is_english(client: TestClient) -> None:
    """Regression guard: clients that omit ``language`` get English behavior."""
    resp = client.post("/v1/rhymes", json={"word": "fire"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "en"
    assert body["meta"]["mode"] == "perfect"


def test_analyze_line_default_language_is_english(client: TestClient) -> None:
    resp = client.post("/v1/analyze-line", json={"line": "fire in the sky"})
    assert resp.status_code == 200
    assert resp.json()["language"] == "en"
