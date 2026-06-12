from fastapi.testclient import TestClient


_DRAFT = (
    "I hear your shadow in the hall\n"
    "I hear your footsteps on the floor\n"
    "\n"
    "[chorus]\n"
    "Hold me in the midnight window\n"
    "Hold me when the city glows"
)


def _cap(body: dict, name: str) -> dict:
    return body["capabilities"][name]


def test_analyze_draft_basic_with_inline_labels(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": _DRAFT},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "en"
    assert _cap(body, "rhyme_scheme")["status"] == "full"
    assert _cap(body, "cadence_patterns")["status"] == "full"
    assert _cap(body, "repetition")["status"] == "full"
    assert _cap(body, "stress_hints")["status"] == "unsupported"

    sections = body["detail"]["sections"]
    assert len(sections) == 2
    labels = [s["label"] for s in sections]
    assert labels == [None, "chorus"]

    chorus = sections[1]
    assert chorus["line_count"] == 2
    assert len(chorus["syllable_pattern"]) == 2
    assert all(n > 0 for n in chorus["syllable_pattern"])
    assert chorus["rhyme_scheme"] in {"AA", "AB"}
    assert chorus["rhyme_scheme_confidence"] in {"full", "partial"}

    opening_sigs = [
        s for s in chorus["repetition_signals"] if s["type"] == "opening_phrase_repeat"
    ]
    assert len(opening_sigs) == 1
    assert opening_sigs[0]["value"].startswith("hold")

    insight_types = {i["type"] for i in body["insights"]}
    assert "syllable_variance" in insight_types
    rep_insights = [i for i in body["insights"] if i["type"] == "repetition_opening"]
    assert len(rep_insights) >= 1
    chorus_rep = next(i for i in rep_insights if i["target"] == chorus["id"])
    assert chorus_rep["severity"] == "info"
    # Phase 5.5: every insight has id, anchor, and typed evidence.
    assert chorus_rep["id"].startswith("ins_")
    assert chorus_rep["anchor"]["scope"] == "section"
    assert chorus_rep["anchor"]["section_id"] == chorus["id"]
    assert chorus_rep["evidence"]["kind"] == "repetition_opening"

    assert body["summary"]["section_count"] == 2
    assert body["summary"]["line_count"] == 4
    assert body["summary"]["insight_count"] == len(body["insights"])
    assert "repetition" in body["summary"]["family_counts"]


def test_analyze_draft_insight_ids_are_stable(client: TestClient) -> None:
    a = client.post(
        "/v1/analyze-draft", json={"language": "en", "content": _DRAFT}
    ).json()
    b = client.post(
        "/v1/analyze-draft", json={"language": "en", "content": _DRAFT}
    ).json()
    assert [i["id"] for i in a["insights"]] == [i["id"] for i in b["insights"]]


def test_analyze_draft_explicit_sections_override_inline(client: TestClient) -> None:
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
    sections = body["detail"]["sections"]
    assert [s["id"] for s in sections] == ["v1", "c1"]
    assert [s["label"] for s in sections] == ["verse", "chorus"]
    chorus = sections[1]
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
    sem = _cap(body, "semantic_repetition")
    motif = _cap(body, "motif_tracking")
    assert sem["status"] == "unsupported"
    assert sem["reason_code"] == "option_not_requested"
    assert motif["status"] == "unsupported"
    assert motif["reason_code"] == "option_not_requested"
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
    assert _cap(body, "semantic_repetition")["status"] == "full"
    semantic = [i for i in body["insights"] if i["type"] == "semantic_repetition"]
    assert semantic, "expected at least one semantic_repetition insight"
    insight = semantic[0]
    assert insight["confidence"] in {"low", "medium", "high"}
    assert insight["evidence"]["kind"] == "semantic_repetition"
    assert "phrases" in insight["evidence"]
    assert "lemmas" in insight["evidence"]
    assert insight["anchor"] is not None


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
    assert _cap(body, "section_contrast")["status"] == "full"
    contrasts = [i for i in body["insights"] if i["type"] == "section_contrast"]
    assert contrasts, "expected a section_contrast insight"
    assert contrasts[0]["evidence"]["contrast_kind"] == "over_similarity"
    assert contrasts[0]["evidence"]["kind"] == "section_contrast"


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
    assert _cap(body, "consistency_hints")["status"] == "full"
    drifts = [i for i in body["insights"] if i["type"] == "perspective_drift"]
    assert drifts, "expected a perspective_drift insight"
    assert drifts[0]["evidence"]["kind"] == "perspective_drift"


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
    cap = _cap(body, "consistency_hints")
    assert cap["status"] == "partial"
    assert cap["reason_code"] == "language_partial_support"


def test_default_request_keeps_m4_capabilities_unsupported(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": _DRAFT},
    )
    body = resp.json()
    assert _cap(body, "section_contrast")["status"] == "unsupported"
    assert _cap(body, "consistency_hints")["status"] == "unsupported"
    types = {i["type"] for i in body["insights"]}
    assert "section_contrast" not in types
    assert "perspective_drift" not in types
    assert "tense_drift" not in types


def test_chorus_repetition_ending_demoted_to_info(client: TestClient) -> None:
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
        s["id"] for s in body["detail"]["sections"] if s["label"] == "chorus"
    )
    chorus_rep = next(i for i in rep_endings if i["target"] == chorus_id)
    # Phase 5.5: hook_context moves out of evidence onto the insight itself.
    assert chorus_rep["hook_context"] is True
    assert chorus_rep["evidence"]["kind"] == "repetition_ending"


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
    assert _cap(body, "motif_tracking")["status"] == "full"
    assert "fire" in body["summary"]["motifs"]


def test_analyze_draft_detects_cross_line_inner_rhymes(client: TestClient) -> None:
    draft = "the cat sat down\non a soft green mat"
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": draft},
    )
    assert resp.status_code == 200
    body = resp.json()
    groups = body["inner_rhymes"]
    assert len(groups) >= 1
    # cat (line 1) and mat (line 2) share a perfect rhyme across lines.
    perfect = next(g for g in groups if g["rhyme_type"] == "perfect")
    by_line = {(o["line_index"], o["normalized"]) for o in perfect["occurrences"]}
    assert (1, "cat") in by_line
    assert (2, "mat") in by_line
    # line numbers are 1-based and global; positions are present.
    for occ in perfect["occurrences"]:
        assert occ["line_index"] >= 1
        assert occ["char_end"] > occ["char_start"]


def test_inner_rhyme_line_index_skips_label_and_blank_lines(
    client: TestClient,
) -> None:
    # Line 1 is a section label and line 2 is blank, neither of which appear
    # in `section.lines` — line_index must still point at the lyric lines
    # (3 and 4), not be off by the two skipped lines.
    draft = "[Verse]\n\nthe cat sat down\non a soft green mat"
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "en", "content": draft},
    )
    assert resp.status_code == 200
    body = resp.json()
    groups = body["inner_rhymes"]
    perfect = next(g for g in groups if g["rhyme_type"] == "perfect")
    by_line = {(o["line_index"], o["normalized"]) for o in perfect["occurrences"]}
    assert (3, "cat") in by_line
    assert (4, "mat") in by_line
