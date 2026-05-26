"""Phase 5 M3 golden-set regression check for /v1/analyze-draft.

Loads bundles tagged with ``kind`` ``draft_semantic_repetition`` or
``draft_motif_tracking`` under ``app/evaluation/golden_sets/`` and
exercises each one against the in-process FastAPI app. Failures are an
editorial signal that lemma quality or clustering thresholds drifted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.evaluation.cases_loader import load_cases


def _as_pairs(kind: str) -> list[tuple[Path, dict[str, Any]]]:
    return [(c.bundle_path, c.payload) for c in load_cases(kinds=[kind])]


_SEMANTIC = _as_pairs("draft_semantic_repetition")
_MOTIF = _as_pairs("draft_motif_tracking")
_CONTRAST = _as_pairs("draft_section_contrast")
_CONSISTENCY = _as_pairs("draft_consistency_hints")


@pytest.mark.parametrize(
    "case_path,case",
    _SEMANTIC,
    ids=[f"{p.parent.name}/{c.get('name', c.get('language', ''))}" for (p, c) in _SEMANTIC],
)
def test_semantic_repetition_golden(
    client: TestClient, case_path: Path, case: dict[str, Any]
) -> None:
    payload = {
        "language": case.get("language", "en"),
        "content": case["content"],
        "options": {"include_semantic_repetition": True},
    }
    resp = client.post("/v1/analyze-draft", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()
    assert body["capabilities"]["semantic_repetition"]["status"] == "full"

    semantic = [i for i in body["insights"] if i["type"] == "semantic_repetition"]
    assert semantic, f"{case_path}: no semantic_repetition insight returned"

    expected = set(case.get("expected_lemmas_any_of", []))
    if expected:
        all_lemmas: set[str] = set()
        for ins in semantic:
            evidence = ins.get("evidence") or {}
            assert evidence.get("kind") == "semantic_repetition"
            all_lemmas.update(evidence.get("lemmas", []))
        overlap = all_lemmas & expected
        assert overlap, (
            f"{case_path}: expected one of {expected} in insight lemmas {all_lemmas}"
        )


@pytest.mark.parametrize(
    "case_path,case",
    _MOTIF,
    ids=[f"{p.parent.name}/{c.get('name', c.get('language', ''))}" for (p, c) in _MOTIF],
)
def test_motif_tracking_golden(
    client: TestClient, case_path: Path, case: dict[str, Any]
) -> None:
    payload = {
        "language": case.get("language", "en"),
        "content": case["content"],
        "options": {"include_motif_tracking": True},
    }
    resp = client.post("/v1/analyze-draft", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()
    assert body["capabilities"]["motif_tracking"]["status"] == "full"

    motifs = set(body["summary"]["motifs"])
    expected = set(case.get("expected_motifs", []))
    if expected:
        overlap = motifs & expected
        assert overlap, (
            f"{case_path}: expected one of {expected} in summary.motifs {motifs}"
        )


@pytest.mark.parametrize(
    "case_path,case",
    _CONTRAST,
    ids=[f"{p.parent.name}/{c.get('name', c.get('language', ''))}" for (p, c) in _CONTRAST],
)
def test_section_contrast_golden(
    client: TestClient, case_path: Path, case: dict[str, Any]
) -> None:
    payload = {
        "language": case.get("language", "en"),
        "content": case["content"],
        "options": {"include_section_contrast": True},
    }
    resp = client.post("/v1/analyze-draft", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()
    assert body["capabilities"]["section_contrast"]["status"] == "full"

    contrasts = [i for i in body["insights"] if i["type"] == "section_contrast"]
    assert contrasts, f"{case_path}: no section_contrast insight returned"

    expected_kind = case.get("expected_contrast_kind")
    if expected_kind:
        kinds = {
            (i.get("evidence") or {}).get("contrast_kind") for i in contrasts
        }
        assert expected_kind in kinds, (
            f"{case_path}: expected contrast_kind {expected_kind!r} in {kinds}"
        )


@pytest.mark.parametrize(
    "case_path,case",
    _CONSISTENCY,
    ids=[f"{p.parent.name}/{c.get('name', c.get('language', ''))}" for (p, c) in _CONSISTENCY],
)
def test_consistency_hints_golden(
    client: TestClient, case_path: Path, case: dict[str, Any]
) -> None:
    payload = {
        "language": case.get("language", "en"),
        "content": case["content"],
        "options": {"include_consistency_hints": True},
    }
    resp = client.post("/v1/analyze-draft", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()
    assert body["capabilities"]["consistency_hints"]["status"] in {"full", "partial"}

    expected_kind = case.get("expected_drift_kind")
    type_for_kind = {
        "perspective": "perspective_drift",
        "tense": "tense_drift",
    }
    if expected_kind:
        expected_type = type_for_kind[expected_kind]
        drifts = [i for i in body["insights"] if i["type"] == expected_type]
        assert drifts, (
            f"{case_path}: expected {expected_type} insight; got types "
            f"{[i['type'] for i in body['insights']]}"
        )
