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
    assert body["capabilities"]["repetition"] == "unsupported"
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
    assert chorus["repetition_signals"] == []

    # Each non-empty section produces a syllable_variance insight.
    insight_types = {i["type"] for i in body["insights"]}
    assert "syllable_variance" in insight_types

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
