import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BASE = Path(__file__).resolve().parents[2] / "app" / "evaluation" / "golden_sets" / "spanish"


def _load(name: str) -> list[dict]:
    return json.loads((_BASE / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load("consonant_rhymes.json"))
def test_consonant_rhyme_coverage(client: TestClient, case: dict) -> None:
    resp = client.post(
        "/v1/rhymes",
        json={"word": case["word"], "language": "es", "mode": "consonant", "limit": 25},
    )
    body = resp.json()
    assert resp.status_code == 200, body
    returned = {r["word"] for r in body["rhymes"]}
    for forbidden in case.get("must_not_contain", []):
        assert forbidden not in returned, f"{forbidden!r} should not be in {case['word']!r} rhymes"
    overlap = set(case["expected_top_rhymes"]) & returned
    assert len(overlap) >= case["min_top_hits"], (
        f"{case['word']!r}: only {sorted(overlap)} of expected {case['expected_top_rhymes']} surfaced"
    )


@pytest.mark.parametrize("case", _load("accent_normalization.json"))
def test_accent_normalization(case: dict) -> None:
    from app.domain.languages.spanish.normalization import normalize_word

    assert normalize_word(case["input"]) == case["normalized"]
