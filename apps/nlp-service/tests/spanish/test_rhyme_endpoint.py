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


def test_spanish_assonant_mode_returns_assonant_type(client: TestClient) -> None:
    # In assonant mode, all returned candidates carry rhyme_type == "assonant".
    # The candidate set is NOT subtracted from consonant matches — in assonant
    # mode the caller wants the full vowel-pattern pool, which may include words
    # that are also consonant rhymes.  Disjointness is only guaranteed in the
    # consonant cascade (where consonant tier appears first and assonant is the
    # remainder), not in standalone assonant mode.
    assonant = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "mode": "assonant", "limit": 25},
    ).json()
    assert assonant["meta"]["mode"] == "assonant"
    assert all(r["rhyme_type"] == "assonant" for r in assonant["rhymes"])
    assert len(assonant["rhymes"]) > 0


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


# --- Phase 5 M1 ---


def test_spanish_candidates_carry_rhyme_family(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "corazón", "language": "es", "limit": 10},
    )
    body = resp.json()
    families = {r["rhyme_family"] for r in body["rhymes"]}
    # Three-syllable -ción words share a multisyllabic tail with corazón.
    assert families & {"consonant", "multisyllabic"}, families
    assert None not in families


def test_spanish_multisyllabic_mode_returns_multi_tier(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={
            "word": "corazón",
            "language": "es",
            "mode": "multisyllabic",
            "limit": 10,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["mode"] == "multisyllabic"
    if body["rhymes"]:
        assert all(r["rhyme_type"] == "multisyllabic" for r in body["rhymes"])
        assert all(r["rhyme_family"] == "multisyllabic" for r in body["rhymes"])


def test_spanish_phrase_ending_trims_leading_article(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={
            "word": "en la noche",
            "language": "es",
            "target_type": "phrase_ending",
            "limit": 5,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["target_type"] == "phrase_ending"
    # Span is the *trimmed* ending; "en" and "la" are leading function words.
    assert body["meta"]["query_span"] == "noche"
    assert body["normalized_word"] == "noche"


def test_spanish_capabilities_block_present(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "corazón", "language": "es"})
    caps = resp.json()["meta"]["capabilities"]
    assert caps["multisyllabic"] == "full"
    assert caps["phrase_ending"] == "full"
