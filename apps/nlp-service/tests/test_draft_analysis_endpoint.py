from fastapi.testclient import TestClient


_DRAFT = (
    "I hear your shadow in the hall\n"
    "I hear your footsteps on the floor\n"
    "\n"
    "[chorus]\n"
    "Hold me in the midnight window\n"
    "Hold me when the city glows"
)


def test_analyze_draft_basic_with_inline_labels(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": _DRAFT},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "en"
    assert body["capabilities"]["rhyme_scheme"] == "full"
    assert body["capabilities"]["cadence_patterns"] == "full"
    assert body["capabilities"]["repetition"] == "full"
    assert body["capabilities"]["stress_hints"] == "unsupported"

    sections = body["sections"]
    assert len(sections) == 2
    labels = [s["label"] for s in sections]
    assert labels == [None, "chorus"]

    chorus = sections[1]
    assert chorus["line_count"] == 2
    assert len(chorus["syllable_pattern"]) == 2
    assert all(n > 0 for n in chorus["syllable_pattern"])
    assert chorus["rhyme_scheme"] in {"AA", "AB"}
    assert chorus["rhyme_scheme_confidence"] in {"full", "partial"}

    # Chorus opens "Hold me..." on both lines — expect an opening_phrase_repeat signal.
    opening_sigs = [
        s for s in chorus["repetition_signals"] if s["type"] == "opening_phrase_repeat"
    ]
    assert len(opening_sigs) == 1
    assert opening_sigs[0]["value"].startswith("hold")

    insight_types = {i["type"] for i in body["insights"]}
    assert "syllable_variance" in insight_types
    # Opening repeat in a chorus should produce an info-severity repetition_opening insight.
    rep_insights = [i for i in body["insights"] if i["type"] == "repetition_opening"]
    assert len(rep_insights) >= 1
    chorus_rep = next(i for i in rep_insights if i["target"] == chorus["id"])
    assert chorus_rep["severity"] == "info"

    assert body["summary"]["section_count"] == 2
    assert body["summary"]["line_count"] == 4


def test_analyze_draft_explicit_sections_override_inline(client: TestClient) -> None:
    # Tell the service the chorus is actually lines 1-2; inline [chorus] is
    # ignored because explicit wins.
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "en",
            "content": _DRAFT,
            "sections": [
                {"id": "v1", "label": "verse", "line_start": 1, "line_end": 2},
                {"id": "c1", "label": "chorus", "line_start": 5, "line_end": 6},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [s["id"] for s in body["sections"]] == ["v1", "c1"]
    assert [s["label"] for s in body["sections"]] == ["verse", "chorus"]
    chorus = body["sections"][1]
    assert chorus["line_start"] == 5 and chorus["line_end"] == 6
    assert len(chorus["syllable_pattern"]) == 2


def test_analyze_draft_blank_input_is_validation_error(client: TestClient) -> None:
    resp = client.post("/v1/analyze-draft", json={"content": "   "})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_analyze_draft_unsupported_language(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "fr", "content": "hello world"},
    )
    assert resp.status_code == 422


def test_analyze_draft_without_options_keeps_phase4_shape(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": _DRAFT},
    )
    assert resp.status_code == 200
    body = resp.json()
    # M3 capabilities default to unsupported when the caller hasn't opted in.
    assert body["capabilities"]["semantic_repetition"] == "unsupported"
    assert body["capabilities"]["motif_tracking"] == "unsupported"
    assert body["summary"]["motifs"] == []
    types = {i["type"] for i in body["insights"]}
    assert "semantic_repetition" not in types
    assert "motif_concentration" not in types


def test_analyze_draft_with_semantic_repetition_option(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "en",
            "content": _DRAFT,
            "options": {"include_semantic_repetition": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["capabilities"]["semantic_repetition"] == "full"
    semantic = [i for i in body["insights"] if i["type"] == "semantic_repetition"]
    assert semantic, "expected at least one semantic_repetition insight"
    insight = semantic[0]
    assert insight["confidence"] in {"low", "medium", "high"}
    assert insight["evidence"] and "phrases" in insight["evidence"]


_SIMILAR_VERSES = (
    "[verse]\nThe sky above is wide and blue\nThe road below is long and true\n"
    "\n[verse]\nThe sky above is wide and blue\nThe road below is long and true\n"
    "\n[chorus]\nWe sing tonight\nWe sing forever"
)

_PERSPECTIVE_FLIP = (
    "[verse]\nI walk alone tonight\nI hold my dreams in sight\nI never let them go\nI keep them safe and slow\n"
    "\n[chorus]\nYou take your time and shine\nYou give your heart for mine\nYou call across the night\nYou make the morning right"
)


def test_analyze_draft_with_section_contrast_option(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "en",
            "content": _SIMILAR_VERSES,
            "options": {"include_section_contrast": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["capabilities"]["section_contrast"] == "full"
    contrasts = [i for i in body["insights"] if i["type"] == "section_contrast"]
    assert contrasts, "expected a section_contrast insight"
    assert contrasts[0]["evidence"]["contrast_kind"] == "over_similarity"


def test_analyze_draft_with_consistency_hints_option(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "en",
            "content": _PERSPECTIVE_FLIP,
            "options": {"include_consistency_hints": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["capabilities"]["consistency_hints"] == "full"
    drifts = [i for i in body["insights"] if i["type"] == "perspective_drift"]
    assert drifts, "expected a perspective_drift insight"


def test_analyze_draft_consistency_hints_spanish_is_partial(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "es",
            "content": "Yo canto solo\nYo busco la luz\n\nTú vienes ya\nTú llamas hoy",
            "options": {"include_consistency_hints": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["capabilities"]["consistency_hints"] == "partial"


def test_default_request_keeps_m4_capabilities_unsupported(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": _DRAFT},
    )
    body = resp.json()
    assert body["capabilities"]["section_contrast"] == "unsupported"
    assert body["capabilities"]["consistency_hints"] == "unsupported"
    types = {i["type"] for i in body["insights"]}
    assert "section_contrast" not in types
    assert "perspective_drift" not in types
    assert "tense_drift" not in types


def test_chorus_repetition_ending_demoted_to_info(client: TestClient) -> None:
    # Two chorus lines closing on "tonight" — Phase 4 emits repetition_ending
    # at severity "info" already; the demotion pass keeps it at "info" but
    # tags the evidence with hook_context.
    draft = (
        "[chorus]\nWe sing tonight\nWe dance tonight\n"
        "\n[verse]\nThe stars are bright\nThe river flows"
    )
    resp = client.post(
        "/v1/analyze-draft", json={"language": "en", "content": draft}
    )
    body = resp.json()
    rep_endings = [
        i for i in body["insights"]
        if i["type"] == "repetition_ending" and i["target"] is not None
    ]
    assert rep_endings, "expected a repetition_ending insight in the chorus"
    chorus_id = next(
        s["id"] for s in body["sections"] if s["label"] == "chorus"
    )
    chorus_rep = next(i for i in rep_endings if i["target"] == chorus_id)
    assert chorus_rep["evidence"] == {"hook_context": True}


def test_analyze_draft_with_motif_tracking_option(client: TestClient) -> None:
    motif_draft = (
        "[verse]\nThe fire on the hill is burning\nThe fire in my chest still calls\n"
        "\n[chorus]\nAll we have is fire and ashes\nAll we have is fire and rain"
    )
    resp = client.post(
        "/v1/analyze-draft",
        json={
            "language": "en",
            "content": motif_draft,
            "options": {"include_motif_tracking": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["capabilities"]["motif_tracking"] == "full"
    assert "fire" in body["summary"]["motifs"]
