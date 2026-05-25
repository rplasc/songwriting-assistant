"""Phase 5 M1 golden-set regression check.

Loads the JSON case files under ``app/evaluation/golden_sets/`` and
exercises each one against the in-process FastAPI app. Each case must:

* return at least one of its ``expected_any_of`` words in the top-N
  result list,
* return zero of its ``must_not_include`` words, and
* attach a non-null ``rhyme_family`` to every candidate.

Failures here are an editorial signal -- they feed M2 ranking work
rather than necessarily indicating a regression. The test is therefore
strict so that quality drift surfaces immediately; if a case turns out
to be fragile or unrealistic, edit the case file rather than the test.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_ROOT = _REPO_ROOT / "app" / "evaluation" / "golden_sets"


def _iter_case_files() -> Iterator[Path]:
    if not _GOLDEN_ROOT.exists():
        return
    yield from _GOLDEN_ROOT.rglob("cases.json")


def _load_cases() -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for path in _iter_case_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        # Skip non-rhyme bundles (e.g., M3 draft semantic golden sets).
        if data.get("kind", "rhyme") != "rhyme":
            continue
        for case in data.get("cases", []):
            out.append((path, data, case))
    return out


CASES = _load_cases()


@pytest.mark.parametrize(
    "case_path,bundle,case",
    CASES,
    ids=[f"{p.parent.name}/{c['query']}" for (p, _, c) in CASES],
)
def test_golden_case(
    client: TestClient,
    case_path: Path,
    bundle: dict[str, Any],
    case: dict[str, Any],
) -> None:
    payload: dict[str, Any] = {
        "word": case["query"],
        "limit": bundle.get("limit", 10),
        "language": case.get("language", "en"),
    }
    if "target_type" in case:
        payload["target_type"] = case["target_type"]
    if "mode" in case:
        payload["mode"] = case["mode"]
    resp = client.post("/v1/rhymes", json=payload)
    assert resp.status_code == 200, f"{case_path}: HTTP {resp.status_code}"
    body = resp.json()
    rhymes = body.get("rhymes", [])
    words = [r["word"] for r in rhymes]

    # Span echo for phrase_ending cases.
    expected_span = case.get("expected_span")
    if expected_span is not None:
        assert body["meta"]["query_span"] == expected_span, (
            f"{case_path}: expected span {expected_span!r}, got "
            f"{body['meta']['query_span']!r}"
        )

    # Every candidate must carry a family.
    families = [r["rhyme_family"] for r in rhymes]
    assert None not in families, f"{case_path}: null rhyme_family in {words}"

    # Forbidden words.
    for forbidden in case.get("must_not_include", []):
        assert forbidden not in words, (
            f"{case_path}: forbidden {forbidden!r} in {words}"
        )

    # Expected hit set: at least one match required.
    expected = case.get("expected_any_of", [])
    if expected:
        overlap = set(words) & set(expected)
        assert overlap, (
            f"{case_path}: none of {expected} in top results {words}"
        )

    # Phase 5 M2: optional diversity check. ``max_cluster_share`` caps the
    # fraction of top-N candidates that may share the same 3-char
    # trailing pattern. Lets the golden set carry expectations about the
    # soft diversity pass alongside the hit set.
    max_cluster = case.get("max_cluster_share")
    if max_cluster is not None and words:
        suffixes: dict[str, int] = {}
        for w in words:
            suf = w[-3:] if len(w) >= 3 else w
            suffixes[suf] = suffixes.get(suf, 0) + 1
        biggest = max(suffixes.values())
        share = biggest / len(words)
        assert share <= max_cluster, (
            f"{case_path}: cluster '{max(suffixes, key=suffixes.get)}' is "
            f"{share:.0%} of top-{len(words)} (cap {max_cluster:.0%})"
        )
