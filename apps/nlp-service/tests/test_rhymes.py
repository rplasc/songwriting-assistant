from fastapi.testclient import TestClient


def test_rhymes_known_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["normalized_word"] == "fire"
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    assert all(r["word"] != "fire" for r in body["rhymes"])
    assert body["meta"] == {"limit": 10, "include_near": False}


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
