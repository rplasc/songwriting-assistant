from fastapi.testclient import TestClient


def test_rhymes_known_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "fire"
    assert body["normalized_query"] == "fire"
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    assert all(r["word"] != "fire" for r in body["rhymes"])
    assert body["target_type"] == "word"
    assert body["mode"] == "perfect"
    assert body["summary"]["requested_limit"] == 10
    assert body["summary"]["returned"] == len(body["rhymes"])
    assert body["capabilities"]["multisyllabic"]["status"] == "full"
    assert body["capabilities"]["phrase_ending"]["status"] == "full"
    assert all(r["rhyme_type"] == "perfect" for r in body["rhymes"])
    assert all(0.0 <= r["score"] <= 1.0 for r in body["rhymes"])
    # Phase 5.5: every candidate gets an id, confidence, and evidence_tags.
    assert all(r["id"].startswith("rhy_") for r in body["rhymes"])
    assert all(r["confidence"] in {"high", "medium", "low"} for r in body["rhymes"])
    assert all(isinstance(r["evidence_tags"], list) for r in body["rhymes"])
    # Without include_metadata, match_reason should be omitted/null.
    assert all(r["match_reason"] is None for r in body["rhymes"])


def test_rhymes_summary_family_counts_match_candidates(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    body = resp.json()
    counts = body["summary"]["family_counts"]
    families = [r["rhyme_family"] for r in body["rhymes"] if r["rhyme_family"]]
    for fam in set(families):
        assert counts.get(fam) == families.count(fam)


def test_rhyme_candidate_id_is_stable(client: TestClient) -> None:
    a = client.post("/v1/rhymes", json={"word": "fire", "limit": 5}).json()
    b = client.post("/v1/rhymes", json={"word": "fire", "limit": 5}).json()
    ids_a = [r["id"] for r in a["rhymes"]]
    ids_b = [r["id"] for r in b["rhymes"]]
    assert ids_a == ids_b


def test_rhymes_unknown_word_with_no_vowel_returns_empty(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "qzqzqz"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pronunciations_found"] is False
    assert body["rhymes"] == []


def test_rhymes_misspelled_word_returns_heuristic_family(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "wundurful", "limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    assert all(r["rhyme_type"] == "family" for r in body["rhymes"])


def test_rhymes_made_up_word_returns_heuristic_family(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "glimble", "limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    assert all(r["rhyme_type"] == "family" for r in body["rhymes"])


def test_rhymes_blank_word_is_validation_error(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "  "})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"


def test_rhymes_limit_is_clamped(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 9999})
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["requested_limit"] == 25
    assert len(body["rhymes"]) <= 25


def test_rhymes_rejects_multi_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "two words"})
    assert resp.status_code == 422


def test_rhymes_near_mode_returns_near_type(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "cat", "mode": "near", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "near"
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


def test_rhymes_near_and_perfect_are_disjoint_polysyllabic(client: TestClient) -> None:
    perfect = client.post("/v1/rhymes", json={"word": "running", "limit": 25}).json()
    near = client.post(
        "/v1/rhymes", json={"word": "running", "mode": "near", "limit": 25}
    ).json()
    perfect_words = {r["word"] for r in perfect["rhymes"]}
    near_words = {r["word"] for r in near["rhymes"]}
    assert perfect_words.isdisjoint(near_words)


def test_rhymes_include_near_flag_is_legacy_alias(client: TestClient) -> None:
    """Phase 1 clients that set `include_near: true` should now get near rhymes."""
    resp = client.post("/v1/rhymes", json={"word": "cat", "include_near": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "near"


def test_rhymes_include_metadata_adds_match_reason(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "fire", "limit": 5, "include_metadata": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(r["match_reason"] for r in body["rhymes"])


def test_rhymes_wonderful_falls_back_to_family_tier(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "wonderful", "limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pronunciations_found"] is True
    assert len(body["rhymes"]) > 0
    types = {r["rhyme_type"] for r in body["rhymes"]}
    assert "family" in types
    assert types.issubset({"perfect", "family", "near"})


def test_rhymes_perfect_mode_keeps_perfect_tier_first(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "cat", "limit": 5})
    body = resp.json()
    assert len(body["rhymes"]) > 0
    assert body["rhymes"][0]["rhyme_type"] == "perfect"


def test_rhymes_family_match_reason_when_metadata_requested(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "wonderful", "limit": 20, "include_metadata": True},
    )
    body = resp.json()
    family = [r for r in body["rhymes"] if r["rhyme_type"] == "family"]
    assert family, "expected at least one family-tier candidate for 'wonderful'"
    assert all(r["match_reason"] == "shared trailing syllable" for r in family)


def test_rhymes_inflection_does_not_top_results(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "run", "limit": 10})
    body = resp.json()
    words = [r["word"] for r in body["rhymes"]]
    if "runs" in words:
        assert words.index("runs") > 0


# --- Phase 5 M1: rhyme_family annotation, multisyllabic mode, phrase_ending ---


def test_rhymes_every_candidate_carries_rhyme_family(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    body = resp.json()
    assert body["rhymes"]
    legal = {"perfect", "multisyllabic", "near", "assonant", "consonant"}
    families = {r["rhyme_family"] for r in body["rhymes"]}
    assert None not in families
    assert families <= legal


def test_rhymes_long_match_classifies_as_multisyllabic(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "wonderful", "limit": 20})
    body = resp.json()
    families = {r["rhyme_family"] for r in body["rhymes"]}
    assert "multisyllabic" in families


def test_rhymes_matched_span_defaults_to_candidate_word(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 5})
    for r in resp.json()["rhymes"]:
        assert r["matched_span"] == r["word"]


def test_rhymes_multisyllabic_mode_returns_only_multi_tier(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "wonderful", "mode": "multisyllabic", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "multisyllabic"
    if body["rhymes"]:
        assert all(r["rhyme_type"] == "multisyllabic" for r in body["rhymes"])
        assert all(r["rhyme_family"] == "multisyllabic" for r in body["rhymes"])
        # Phase 5.5: multisyllabic candidates carry the multisyllabic key tag.
        assert all(
            "multisyllabic_key_match" in r["evidence_tags"]
            for r in body["rhymes"]
        )


def test_rhymes_multisyllabic_mode_empty_for_short_word(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "cat", "mode": "multisyllabic", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rhymes"] == []


def test_rhymes_phrase_ending_accepts_multi_token_input(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "hold me", "target_type": "phrase_ending", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_type"] == "phrase_ending"
    assert body["query"] == "hold me"
    assert body["mode"] == "perfect"
    assert body["rhymes"]
    # Phrase ending matches get the phrase_ending_match tag.
    assert all("phrase_ending_match" in r["evidence_tags"] for r in body["rhymes"])


def test_rhymes_phrase_ending_trims_leading_function_words(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={
            "word": "in the night",
            "target_type": "phrase_ending",
            "limit": 5,
        },
    )
    body = resp.json()
    assert body["normalized_query"] == "night"


def test_rhymes_rejects_multi_word_for_word_target(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "two words"})
    assert resp.status_code == 422


def test_rhymes_capabilities_block_present(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire"})
    caps = resp.json()["capabilities"]
    assert caps["multisyllabic"]["status"] == "full"
    assert caps["phrase_ending"]["status"] == "full"
    assert caps["multisyllabic"]["reason_code"] is None


# --- Phase 5 M2 ---


def test_phrase_ending_excludes_all_span_tokens(client: TestClient) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": "walking away", "target_type": "phrase_ending", "limit": 10},
    )
    body = resp.json()
    words = {r["word"] for r in body["rhymes"]}
    assert "walking" not in words
    assert "away" not in words


def test_top_results_for_high_cluster_query_are_diversified(client: TestClient) -> None:
    resp = client.post("/v1/rhymes", json={"word": "fire", "limit": 10})
    rhymes = resp.json()["rhymes"]
    assert rhymes
    suffixes = {r["word"][-3:] for r in rhymes if len(r["word"]) >= 3}
    assert len(suffixes) >= 4, f"top-10 collapsed onto {suffixes}"
