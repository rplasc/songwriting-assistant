"""Phase 5.5 Milestone 3 regression-report service.

Walks the golden bundles, dispatches each case to its kind-specific
runner, and aggregates pass/fail + latency stats. The same service
backs both the CLI runner and the HTTP endpoint.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable
from datetime import datetime, timezone

from app.evaluation import case_runners
from app.evaluation.cases_loader import LoadedCase, load_cases
from app.schemas.evaluation import (
    CONTRACT_VERSION,
    CaseResult,
    EvaluationReportResponse,
    KindStats,
    ReportTotals,
)
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.draft_compare_service import DraftCompareService
from app.services.language_router import LanguageRouter


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return round(values[0], 3)
    sorted_vals = sorted(values)
    # Linear interpolation; matches the simple "nearest-rank-ish" feel
    # we want from a small N without pulling in numpy.
    k = (len(sorted_vals) - 1) * pct
    floor = int(k)
    ceil = min(floor + 1, len(sorted_vals) - 1)
    if floor == ceil:
        return round(sorted_vals[floor], 3)
    frac = k - floor
    interpolated = sorted_vals[floor] + (sorted_vals[ceil] - sorted_vals[floor]) * frac
    return round(interpolated, 3)


def _aggregate(group: list[CaseResult]) -> KindStats:
    latencies = [c.elapsed_ms for c in group]
    return KindStats(
        cases=len(group),
        passed=sum(1 for c in group if c.passed),
        failed=sum(1 for c in group if not c.passed),
        p50_ms=_percentile(latencies, 0.5),
        p95_ms=_percentile(latencies, 0.95),
        max_ms=round(max(latencies), 3) if latencies else 0.0,
    )


class EvaluationReportService:
    """One instance per app; depends on already-built services."""

    def __init__(
        self,
        *,
        language_router: LanguageRouter,
        draft_analysis_service: DraftAnalysisService,
        draft_compare_service: DraftCompareService,
    ) -> None:
        self._language_router = language_router
        self._analysis = draft_analysis_service
        self._compare = draft_compare_service

    def generate(
        self,
        *,
        kinds: Iterable[str] | None = None,
        languages: Iterable[str] | None = None,
        include_cases: bool = False,
    ) -> EvaluationReportResponse:
        cases = load_cases(kinds=kinds, languages=languages)
        results: list[CaseResult] = [self._run_one(c) for c in cases]

        totals = ReportTotals(
            cases=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed),
            skipped=0,
        )

        by_kind: dict[str, KindStats] = {}
        groups_by_kind: dict[str, list[CaseResult]] = {}
        for r in results:
            groups_by_kind.setdefault(r.kind, []).append(r)
        for kind, group in groups_by_kind.items():
            by_kind[kind] = _aggregate(group)

        by_language: dict[str, KindStats] = {}
        groups_by_lang: dict[str, list[CaseResult]] = {}
        for r in results:
            groups_by_lang.setdefault(r.language, []).append(r)
        for lang, group in groups_by_lang.items():
            by_language[lang] = _aggregate(group)

        return EvaluationReportResponse(
            generated_at=datetime.now(timezone.utc).isoformat(),
            totals=totals,
            by_kind=by_kind,
            by_language=by_language,
            cases=results if include_cases else None,
            contract_version=CONTRACT_VERSION,
        )

    def _run_one(self, case: LoadedCase) -> CaseResult:
        if case.kind == "rhyme":
            return case_runners.run_rhyme(case, self._language_router)
        if case.kind == "draft_semantic_repetition":
            return case_runners.run_semantic_repetition(
                case, self._analysis, self._language_router
            )
        if case.kind == "draft_motif_tracking":
            return case_runners.run_motif_tracking(
                case, self._analysis, self._language_router
            )
        if case.kind == "draft_section_contrast":
            return case_runners.run_section_contrast(
                case, self._analysis, self._language_router
            )
        if case.kind == "draft_consistency_hints":
            return case_runners.run_consistency_hints(
                case, self._analysis, self._language_router
            )
        if case.kind == "draft_compare":
            return case_runners.run_draft_compare(
                case, self._compare, self._language_router
            )
        return CaseResult(
            kind=case.kind,
            language=case.language,  # type: ignore[arg-type]
            name=case.name,
            passed=False,
            failures=[f"no runner registered for kind {case.kind!r}"],
            elapsed_ms=0.0,
        )


__all__ = ["EvaluationReportService"]
