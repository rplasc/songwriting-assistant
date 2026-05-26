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

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.evaluation.cases_loader import LoadedCase, load_cases

CASES: list[LoadedCase] = load_cases(kinds=["rhyme"])


@pytest.mark.parametrize(
    "loaded",
    CASES,
    ids=[f"{c.bundle_path.parent.name}/{c.name}" for c in CASES],
)
def test_golden_case(client: TestClient, loaded: LoadedCase) -> None:
    case_path: Path = loaded.bundle_path
    case: dict[str, Any] = loaded.payload
    payload: dict[str, Any] = {
        "word": case["query"],
        "limit": 10,
        "language": loaded.language,
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

    # Span echo for phrase_ending cases. Phase 5.5: the request's
    # ``word`` is echoed at top-level as ``query``; the trimmed span is
    # reflected in ``normalized_query`` for phrase_ending.
    expected_span = case.get("expected_span")
    if expected_span is not None:
        # The expected_span is the trimmed phrase ending; assert it shows
        # up as either the normalized query (post-trim) or the query.
        echoed = body.get("normalized_query") or body.get("query")
        assert expected_span in {body.get("normalized_query"), body.get("query")}, (
            f"{case_path}: expected span {expected_span!r}, got {echoed!r}"
        )

    # Every candidate must carry a family.
    families = [r["rhyme_family"] for r in rhymes]
    assert None not in families, f"{case_path}: null rhyme_family in {words}"

    # Phase 5.5: every candidate must also carry an id, confidence, and tags.
    for r in rhymes:
        assert r["id"].startswith("rhy_"), f"{case_path}: missing id on {r}"
        assert r["confidence"] in {"high", "medium", "low"}
        assert isinstance(r["evidence_tags"], list)

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
