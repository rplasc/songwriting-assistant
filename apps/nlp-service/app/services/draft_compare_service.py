"""Phase 5.5 Milestone 2 compare orchestrator.

Calls ``DraftAnalysisService.analyze`` twice (once per revision) with
the matching Phase 5 options forced on so the delta rules have the
data they need, then runs the delta orchestrator and builds the
compare response.
"""

from __future__ import annotations

from app.core.logging import get_logger, timed
from app.domain.draft_compare.draft_compare_rules import compute_compare
from app.domain.response_contracts.capability_reason_mapper import (
    compare_capabilities,
)
from app.domain.response_contracts.revision_hash import (
    make_compare_analysis_id,
    make_revision_hash,
    options_signature,
)
from app.schemas.draft_analysis import (
    DraftAnalysisOptions,
    DraftAnalysisRequest,
    DraftAnalysisResponse,
)
from app.schemas.draft_compare import (
    CompareCapabilities,
    CompareSummary,
    DraftCompareOptions,
    DraftCompareRequest,
    DraftCompareResponse,
    DraftRevision,
    DraftSide,
)
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.language_router import LanguageContext


_logger = get_logger("nlp.draft_compare")


_DEFAULT_OPTIONS = DraftCompareOptions()


class DraftCompareService:
    """One instance per app; delegates per-side analysis to DraftAnalysisService."""

    def __init__(self, analysis_service: DraftAnalysisService) -> None:
        self._analysis = analysis_service

    def compare(
        self,
        request: DraftCompareRequest,
        context: LanguageContext,
    ) -> DraftCompareResponse:
        opts = request.options or _DEFAULT_OPTIONS
        analysis_opts = _analysis_options_for(opts)
        sig = options_signature(
            compare_motifs=opts.compare_motifs,
            compare_repetition=opts.compare_repetition,
            compare_sections=opts.compare_sections,
            compare_consistency=opts.compare_consistency,
        )

        with timed(
            _logger,
            "compare.analyze_previous",
            language=request.language,
            chars=len(request.previous.content),
        ):
            previous_analysis = self._analyze_side(
                request.language, request.previous, analysis_opts, context
            )
        with timed(
            _logger,
            "compare.analyze_current",
            language=request.language,
            chars=len(request.current.content),
        ):
            current_analysis = self._analyze_side(
                request.language, request.current, analysis_opts, context
            )

        previous_hash = make_revision_hash(
            language=request.language,
            content=request.previous.content,
            options_signature=sig,
        )
        current_hash = make_revision_hash(
            language=request.language,
            content=request.current.content,
            options_signature=sig,
        )
        analysis_id = make_compare_analysis_id(
            previous_hash=previous_hash,
            current_hash=current_hash,
            options_signature=sig,
        )

        with timed(_logger, "compare.compute_deltas", language=request.language):
            result = compute_compare(
                previous_analysis,
                current_analysis,
                compare_motifs=opts.compare_motifs,
                compare_repetition=opts.compare_repetition,
                compare_sections=opts.compare_sections,
                compare_consistency=opts.compare_consistency,
                previous_had_explicit_ids=request.previous.sections is not None,
                current_had_explicit_ids=request.current.sections is not None,
            )

        capabilities = compare_capabilities(
            compare_motifs=opts.compare_motifs,
            compare_repetition=opts.compare_repetition,
            compare_sections=opts.compare_sections,
            compare_consistency=opts.compare_consistency,
        )

        summary = CompareSummary(
            motif_delta_count=result.motif_delta_count,
            repetition_delta_count=result.repetition_delta_count,
            section_delta_count=result.section_delta_count,
            consistency_delta_count=result.consistency_delta_count,
            family_counts=result.family_counts,
            unmatched_previous_section_ids=[
                s.id for s in result.match.unmatched_previous
            ],
            unmatched_current_section_ids=[
                s.id for s in result.match.unmatched_current
            ],
        )

        return DraftCompareResponse(
            analysis_id=analysis_id,
            language=request.language,
            title=request.title,
            previous=DraftRevision(
                revision_hash=previous_hash, analysis=previous_analysis
            ),
            current=DraftRevision(
                revision_hash=current_hash, analysis=current_analysis
            ),
            summary=summary,
            insights=result.insights,
            capabilities=CompareCapabilities(**capabilities),
        )

    def _analyze_side(
        self,
        language: str,
        side: DraftSide,
        options: DraftAnalysisOptions,
        context: LanguageContext,
    ) -> DraftAnalysisResponse:
        single_request = DraftAnalysisRequest(
            language=language,  # type: ignore[arg-type]
            title=None,
            content=side.content,
            sections=side.sections,
            options=options,
        )
        return self._analysis.analyze(single_request, context)


def _analysis_options_for(opts: DraftCompareOptions) -> DraftAnalysisOptions:
    # Force the matching single-draft options on so delta rules have
    # complete data. Semantic repetition isn't yet a compare delta but
    # we leave it off here to avoid wasting work.
    return DraftAnalysisOptions(
        include_semantic_repetition=False,
        include_motif_tracking=opts.compare_motifs,
        include_section_contrast=False,
        include_consistency_hints=opts.compare_consistency,
    )


__all__ = ["DraftCompareService"]
