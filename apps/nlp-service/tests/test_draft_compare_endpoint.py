from fastapi.testclient import TestClient


_DRAFT_PREV = (
    "[verse]\nThe fire on the hill is burning\nThe fire in my chest still calls\n"
    "\n[chorus]\nHold me in the midnight window\nHold me when the city glows"
)
_DRAFT_CURRENT = (
    "[verse]\nThe rain across the road is falling\nThe rain on every window calls\n"
    "\n[chorus]\nHold me in the midnight window\nHold me when the city glows"
)


def _payload(prev_content: str, cur_content: str, **opts) -> dict:
    body: dict = {
        "language": "en",
        "previous": {"content": prev_content},
        "current": {"content": cur_content},
    }
    if opts:
        body["options"] = opts
    return body


def test_compare_identical_drafts_yields_no_deltas(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft-compare", json=_payload(_DRAFT_PREV, _DRAFT_PREV)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["previous"]["revision_hash"] == body["current"]["revision_hash"]
    assert body["insights"] == []
    summary = body["summary"]
    assert summary["motif_delta_count"] == 0
    assert summary["repetition_delta_count"] == 0
    assert summary["section_delta_count"] == 0
    assert summary["consistency_delta_count"] == 0


def test_compare_analysis_id_is_deterministic(client: TestClient) -> None:
    a = client.post(
        "/v1/analyze-draft-compare", json=_payload(_DRAFT_PREV, _DRAFT_CURRENT)
    ).json()
    b = client.post(
        "/v1/analyze-draft-compare", json=_payload(_DRAFT_PREV, _DRAFT_CURRENT)
    ).json()
    assert a["analysis_id"] == b["analysis_id"]
    assert a["previous"]["revision_hash"] == b["previous"]["revision_hash"]
    assert a["current"]["revision_hash"] == b["current"]["revision_hash"]
    assert [i["id"] for i in a["insights"]] == [i["id"] for i in b["insights"]]


def test_compare_motif_swap_emits_motif_deltas(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft-compare", json=_payload(_DRAFT_PREV, _DRAFT_CURRENT)
    )
    assert resp.status_code == 200
    body = resp.json()
    motif_types = [
        i["type"] for i in body["insights"] if i["type"].startswith("motif_")
    ]
    # "fire" should leave (added/strengthened in prev only) and "rain" should
    # appear in current — at minimum we expect both motif_added and
    # motif_removed insights or strengthened/weakened equivalents.
    assert motif_types, f"expected motif deltas, got insights {body['insights']}"
    assert body["summary"]["motif_delta_count"] == len(motif_types)


def test_compare_disabled_motif_capability_marks_option_not_requested(
    client: TestClient,
) -> None:
    resp = client.post(
        "/v1/analyze-draft-compare",
        json=_payload(
            _DRAFT_PREV,
            _DRAFT_CURRENT,
            compare_motifs=False,
            compare_repetition=True,
            compare_sections=True,
            compare_consistency=False,
        ),
    )
    assert resp.status_code == 200
    body = resp.json()
    caps = body["capabilities"]
    assert caps["compare_motifs"]["status"] == "unsupported"
    assert caps["compare_motifs"]["reason_code"] == "option_not_requested"
    assert caps["compare_repetition"]["status"] == "full"
    assert all(
        not i["type"].startswith("motif_") for i in body["insights"]
    )


def test_compare_structure_mismatch_surfaces_in_summary(client: TestClient) -> None:
    prev = "[verse]\na\nb\n\n[chorus]\nc\nd"
    cur = "[verse]\na\nb\n\n[bridge]\ne\nf\n\n[chorus]\nc\nd"
    resp = client.post("/v1/analyze-draft-compare", json=_payload(prev, cur))
    assert resp.status_code == 200
    body = resp.json()
    summary = body["summary"]
    # The bridge section should land in unmatched_current rather than
    # generating shift insights against verse/chorus.
    assert summary["unmatched_current_section_ids"], summary


def test_compare_blank_content_is_validation_error(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft-compare",
        json={
            "language": "en",
            "previous": {"content": "  "},
            "current": {"content": "valid line"},
        },
    )
    assert resp.status_code == 422


def test_compare_response_includes_full_per_side_analyses(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft-compare", json=_payload(_DRAFT_PREV, _DRAFT_CURRENT)
    )
    body = resp.json()
    # Each side carries a full DraftAnalysisResponse with the M0/M1 shape.
    for side in ("previous", "current"):
        analysis = body[side]["analysis"]
        assert "capabilities" in analysis
        assert "detail" in analysis
        assert "sections" in analysis["detail"]
        assert analysis["capabilities"]["rhyme_scheme"]["status"] == "full"
