from fastapi.testclient import TestClient


_DRAFT_LABELED = (
    "[verse]\n"
    "yo te quiero más que ayer\n"
    "y mañana te querré\n"
    "[chorus]\n"
    "ven conmigo a caminar\n"
    "ven conmigo a respirar"
)


def test_spanish_draft_with_labels(client: TestClient) -> None:
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "es", "content": _DRAFT_LABELED},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "es"
    assert body["capabilities"]["cadence_patterns"] == "full"
    assert body["capabilities"]["rhyme_scheme"] == "full"

    sections = body["sections"]
    assert [s["label"] for s in sections] == ["verse", "chorus"]

    chorus = sections[1]
    # Both chorus lines end in -ar (caminar / respirar) → same consonant rhyme.
    assert chorus["rhyme_scheme"] == "AA"
    assert chorus["rhyme_scheme_confidence"] == "full"
    assert all(n > 0 for n in chorus["syllable_pattern"])


def test_spanish_draft_stanza_fallback(client: TestClient) -> None:
    content = (
        "yo te quiero más que ayer\n"
        "y mañana te querré\n"
        "\n"
        "ven conmigo a caminar\n"
        "ven conmigo a respirar"
    )
    resp = client.post(
        "/v1/analyze-draft",
        json={"language": "es", "content": content},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sections"]) == 2
    assert all(s["label"] is None for s in body["sections"])
    assert body["sections"][1]["rhyme_scheme"] == "AA"
