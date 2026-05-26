"""Per-kind case runners.

Each runner accepts a ``LoadedCase`` plus the services it needs and
returns a ``CaseResult``. Assertion logic mirrors the existing
``tests/test_phase5_*_golden_sets.py`` files so the regression runner
and pytest agree.

Runners are pure functions over the services — they don't go through
HTTP, so they work in CLI mode without a running server.
"""

from __future__ import annotations

import time
from typing import Any

from app.domain.response_contracts.rhyme_evidence_tagger import tag_candidate
from app.evaluation.cases_loader import LoadedCase
from app.schemas.draft_analysis import (
    DraftAnalysisOptions,
    DraftAnalysisRequest,
    SectionInput,
)
from app.schemas.draft_compare import (
    DraftCompareOptions,
    DraftCompareRequest,
    DraftSide,
)
from app.schemas.evaluation import CaseResult
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.draft_compare_service import DraftCompareService
from app.services.language_router import LanguageContext, LanguageRouter


def _result(
    case: LoadedCase, failures: list[str], elapsed_ms: float
) -> CaseResult:
    return CaseResult(
        kind=case.kind,
        language=case.language,  # type: ignore[arg-type]
        name=case.name,
        passed=not failures,
        failures=failures,
        elapsed_ms=round(elapsed_ms, 3),
    )


def _now_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0


# --- rhyme ---


def run_rhyme(case: LoadedCase, language_router: LanguageRouter) -> CaseResult:
    payload = case.payload
    failures: list[str] = []
    started = time.perf_counter()
    ctx: LanguageContext = language_router.get(case.language)
    lookup = ctx.rhyme_service.find_rhymes(
        payload["query"],
        payload.get("limit", 10),
        mode=payload.get("mode"),
        target_type=payload.get("target_type", "word"),
        include_metadata=False,
    )
    tagged = [
        tag_candidate(
            c,
            query=payload["query"],
            language=case.language,
            target_type=payload.get("target_type", "word"),
            pronunciations_found=lookup.pronunciations_found,
        )
        for c in lookup.candidates
    ]
    elapsed = _now_ms(started)

    words = [c.word for c in tagged]
    families = [c.rhyme_family for c in tagged]

    expected_span = payload.get("expected_span")
    if expected_span is not None and lookup.normalized != expected_span:
        # Phrase ending requests echo the normalized span; align with the
        # M0/M1 endpoint behavior.
        if expected_span != payload["query"]:
            failures.append(
                f"expected span {expected_span!r}, got {lookup.normalized!r}"
            )

    if any(f is None for f in families):
        failures.append(f"null rhyme_family in {words}")

    for forbidden in payload.get("must_not_include", []) or []:
        if forbidden in words:
            failures.append(f"forbidden {forbidden!r} in {words}")

    expected_any_of = payload.get("expected_any_of") or []
    if expected_any_of and not (set(words) & set(expected_any_of)):
        failures.append(f"none of {expected_any_of} in top results {words}")

    max_cluster = payload.get("max_cluster_share")
    if max_cluster is not None and words:
        suffixes: dict[str, int] = {}
        for w in words:
            suf = w[-3:] if len(w) >= 3 else w
            suffixes[suf] = suffixes.get(suf, 0) + 1
        biggest = max(suffixes.values())
        share = biggest / len(words)
        if share > max_cluster:
            failures.append(
                f"cluster share {share:.2f} exceeds cap {max_cluster:.2f}"
            )

    return _result(case, failures, elapsed)


# --- draft analyze helpers ---


def _section_inputs(payload: dict[str, Any]) -> list[SectionInput] | None:
    raw = payload.get("sections")
    if not raw:
        return None
    return [SectionInput(**s) for s in raw]


def _analyze(
    case: LoadedCase,
    analysis_service: DraftAnalysisService,
    language_router: LanguageRouter,
    *,
    options: DraftAnalysisOptions,
) -> tuple[Any, float]:
    started = time.perf_counter()
    ctx = language_router.get(case.language)
    request = DraftAnalysisRequest(
        language=case.language,  # type: ignore[arg-type]
        title=None,
        content=case.payload["content"],
        sections=_section_inputs(case.payload),
        options=options,
    )
    response = analysis_service.analyze(request, ctx)
    return response, _now_ms(started)


# --- draft_semantic_repetition ---


def run_semantic_repetition(
    case: LoadedCase,
    analysis_service: DraftAnalysisService,
    language_router: LanguageRouter,
) -> CaseResult:
    response, elapsed = _analyze(
        case,
        analysis_service,
        language_router,
        options=DraftAnalysisOptions(include_semantic_repetition=True),
    )
    failures: list[str] = []
    if response.capabilities.semantic_repetition.status != "full":
        failures.append("semantic_repetition capability not full")
    semantic = [i for i in response.insights if i.type == "semantic_repetition"]
    if not semantic:
        failures.append("no semantic_repetition insight returned")
    expected = set(case.payload.get("expected_lemmas_any_of", []))
    if expected and semantic:
        all_lemmas: set[str] = set()
        for ins in semantic:
            ev = ins.evidence
            lemmas = getattr(ev, "lemmas", None) or []
            all_lemmas.update(lemmas)
        if not (all_lemmas & expected):
            failures.append(
                f"expected one of {sorted(expected)} in lemmas {sorted(all_lemmas)}"
            )
    return _result(case, failures, elapsed)


# --- draft_motif_tracking ---


def run_motif_tracking(
    case: LoadedCase,
    analysis_service: DraftAnalysisService,
    language_router: LanguageRouter,
) -> CaseResult:
    response, elapsed = _analyze(
        case,
        analysis_service,
        language_router,
        options=DraftAnalysisOptions(include_motif_tracking=True),
    )
    failures: list[str] = []
    if response.capabilities.motif_tracking.status != "full":
        failures.append("motif_tracking capability not full")
    motifs = set(response.summary.motifs)
    expected = set(case.payload.get("expected_motifs", []))
    if expected and not (motifs & expected):
        failures.append(
            f"expected one of {sorted(expected)} in motifs {sorted(motifs)}"
        )
    return _result(case, failures, elapsed)


# --- draft_section_contrast ---


def run_section_contrast(
    case: LoadedCase,
    analysis_service: DraftAnalysisService,
    language_router: LanguageRouter,
) -> CaseResult:
    response, elapsed = _analyze(
        case,
        analysis_service,
        language_router,
        options=DraftAnalysisOptions(include_section_contrast=True),
    )
    failures: list[str] = []
    if response.capabilities.section_contrast.status != "full":
        failures.append("section_contrast capability not full")
    contrasts = [i for i in response.insights if i.type == "section_contrast"]
    if not contrasts:
        failures.append("no section_contrast insight returned")
    expected_kind = case.payload.get("expected_contrast_kind")
    if expected_kind and contrasts:
        kinds = {
            getattr(i.evidence, "contrast_kind", None) for i in contrasts
        }
        if expected_kind not in kinds:
            failures.append(f"expected contrast_kind {expected_kind!r} in {kinds}")
    return _result(case, failures, elapsed)


# --- draft_consistency_hints ---


def run_consistency_hints(
    case: LoadedCase,
    analysis_service: DraftAnalysisService,
    language_router: LanguageRouter,
) -> CaseResult:
    response, elapsed = _analyze(
        case,
        analysis_service,
        language_router,
        options=DraftAnalysisOptions(include_consistency_hints=True),
    )
    failures: list[str] = []
    cap_status = response.capabilities.consistency_hints.status
    if cap_status not in {"full", "partial"}:
        failures.append(f"consistency_hints capability {cap_status!r}")
    expected_kind = case.payload.get("expected_drift_kind")
    type_for_kind = {
        "perspective": "perspective_drift",
        "tense": "tense_drift",
    }
    if expected_kind:
        expected_type = type_for_kind.get(expected_kind)
        if expected_type is None:
            failures.append(f"unknown expected_drift_kind {expected_kind!r}")
        else:
            drifts = [i for i in response.insights if i.type == expected_type]
            if not drifts:
                failures.append(
                    f"expected {expected_type} insight; got types "
                    f"{[i.type for i in response.insights]}"
                )
    return _result(case, failures, elapsed)


# --- draft_compare ---


def run_draft_compare(
    case: LoadedCase,
    compare_service: DraftCompareService,
    language_router: LanguageRouter,
) -> CaseResult:
    payload = case.payload
    options_payload = payload.get("options") or {}
    options = DraftCompareOptions(**options_payload)
    started = time.perf_counter()
    ctx = language_router.get(case.language)
    request = DraftCompareRequest(
        language=case.language,  # type: ignore[arg-type]
        title=None,
        previous=DraftSide(**payload["previous"]),
        current=DraftSide(**payload["current"]),
        options=options,
    )
    response = compare_service.compare(request, ctx)
    elapsed = _now_ms(started)

    failures: list[str] = []
    insight_types = {i.type for i in response.insights}

    any_of = set(payload.get("expected_insight_types_any_of", []))
    if any_of and not (insight_types & any_of):
        failures.append(
            f"expected one of {sorted(any_of)} in insight types {sorted(insight_types)}"
        )

    forbidden = set(payload.get("expected_insight_types_must_not_include", []))
    intersection = insight_types & forbidden
    if intersection:
        failures.append(
            f"forbidden insight types present: {sorted(intersection)}"
        )

    expected_summary = payload.get("expected_summary") or {}
    summary = response.summary
    for field in (
        "motif_delta_count",
        "repetition_delta_count",
        "section_delta_count",
        "consistency_delta_count",
    ):
        if field in expected_summary:
            actual = getattr(summary, field)
            if actual != expected_summary[field]:
                failures.append(
                    f"{field}: expected {expected_summary[field]}, got {actual}"
                )

    return _result(case, failures, elapsed)


__all__ = [
    "run_consistency_hints",
    "run_draft_compare",
    "run_motif_tracking",
    "run_rhyme",
    "run_section_contrast",
    "run_semantic_repetition",
]
