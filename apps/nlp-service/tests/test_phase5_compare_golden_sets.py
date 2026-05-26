"""Phase 5.5 M3 draft-compare golden-set regression test.

Loads bundles tagged ``kind="draft_compare"`` and exercises each one
against the in-process FastAPI app. Cases assert which insight types
should (or must not) appear, and optionally pin specific delta counts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.evaluation.cases_loader import load_cases


_CASES = [(c.bundle_path, c.payload) for c in load_cases(kinds=["draft_compare"])]


@pytest.mark.parametrize(
    "case_path,case",
    _CASES,
    ids=[f"{p.parent.name}/{c.get('name', '')}" for (p, c) in _CASES],
)
def test_draft_compare_golden(
    client: TestClient, case_path: Path, case: dict[str, Any]
) -> None:
    payload = {
        "language": case.get("language", "en"),
        "previous": case["previous"],
        "current": case["current"],
        "options": case.get("options"),
    }
    if payload["options"] is None:
        del payload["options"]
    resp = client.post("/v1/analyze-draft-compare", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()

    insight_types = {i["type"] for i in body["insights"]}

    any_of = set(case.get("expected_insight_types_any_of", []))
    if any_of:
        assert insight_types & any_of, (
            f"{case_path}: expected one of {sorted(any_of)} in {sorted(insight_types)}"
        )

    forbidden = set(case.get("expected_insight_types_must_not_include", []))
    if forbidden:
        intersection = insight_types & forbidden
        assert not intersection, (
            f"{case_path}: forbidden types present: {sorted(intersection)}"
        )

    expected_summary = case.get("expected_summary") or {}
    summary = body["summary"]
    for field, value in expected_summary.items():
        assert summary.get(field) == value, (
            f"{case_path}: summary.{field}: expected {value}, got {summary.get(field)}"
        )
