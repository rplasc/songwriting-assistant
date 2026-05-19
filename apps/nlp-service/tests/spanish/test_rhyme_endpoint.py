from fastapi.testclient import TestClient


def test_spanish_default_mode_is_consonant(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "corazón", "language": "es"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "es"
    assert body["meta"]["mode"] == "consonant"
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    types = {r["rhyme_type"] for r in body["rhymes"]}
    assert types.issubset({"consonant", "assonant"})


def test_spanish_consonant_returns_consonant_first(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "mode": "consonant", "limit": 20},
    )
    body = resp.json()
    assert body["rhymes"][0]["rhyme_type"] == "consonant"


def test_spanish_assonant_mode_excludes_consonant_matches(client: TestClient) -> None:
    consonant = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "mode": "consonant", "limit": 25},
    ).json()
    assonant = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "mode": "assonant", "limit": 25},
    ).json()
    assert assonant["meta"]["mode"] == "assonant"
    cons_words = {r["word"] for r in consonant["rhymes"] if r["rhyme_type"] == "consonant"}
    asson_words = {r["word"] for r in assonant["rhymes"]}
    assert cons_words.isdisjoint(asson_words)
    assert all(r["rhyme_type"] == "assonant" for r in assonant["rhymes"])


def test_spanish_rejects_english_mode(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "mode": "perfect"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_mode"


def test_english_rejects_spanish_mode(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "fire", "language": "en", "mode": "consonant"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_mode"


def test_corazón_top_consonant_rhymes_include_expected(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "limit": 25},
    )
    body = resp.json()
    words = {r["word"] for r in body["rhymes"]}
    # Highly common 3-syllable -ción/-sión words share corazón's tail and
    # match its syllable count, so they dominate the top of the result.
    expected = {
        "situación",
        "atención",
        "población",
        "relación",
        "dirección",
        "producción",
        "opinión",
        "construcción",
        "decisión",
    }
    overlap = words & expected
    assert len(overlap) >= 3, f"expected at least 3 of {expected} in {words}"


def test_normalized_word_round_trips(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "CORAZÓN", "language": "es"},
    )
    body = resp.json()
    assert body["normalized_word"] == "corazón"
