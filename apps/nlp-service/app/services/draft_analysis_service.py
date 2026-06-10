"""Compose line-level primitives into draft-level analysis.

Phase 5.5: response shape is product-stable — each insight carries a
deterministic id, an anchor, and typed evidence. Capabilities are
``Capability`` models with explicit reason codes. Sections move under
``detail`` so the top-level summary stays UI-friendly.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.core.logging import get_logger, timed
from app.domain.draft_analysis.cadence_rules import classify_pattern
from app.domain.draft_analysis.hook_demotion import demote_inside_hooks
from app.domain.draft_analysis.repetition_rules import (
    RepetitionSignal as DomainRepetitionSignal,
    detect_draft_overuse,
    detect_section_signals,
)
from app.domain.draft_analysis.rhyme_scheme_rules import assign_scheme
from app.domain.draft_analysis.section_parser import (
    ParsedSection,
    parse_sections,
)
from app.domain.heuristic_g2p import heuristic_phoneme_tails
from app.domain.languages.spanish.g2p import g2p as spanish_g2p
from app.domain.languages.spanish.rhyme_rules import consonant_rhyme_key
from app.domain.response_contracts.capability_reason_mapper import (
    base_capabilities,
    opt_in_capability,
)
from app.domain.response_contracts.evidence_anchor_builder import (
    build_consistency_insight,
    build_motif_insight,
    build_repetition_ending_insight,
    build_repetition_opening_insight,
    build_section_contrast_insight,
    build_semantic_repetition_insight,
    build_syllable_variance_insight,
    build_word_overuse_insight,
)
from app.domain.rhyme.inner_rhyme_rules import (
    find_inner_rhyme_groups,
    phonemes_for_context,
)
from app.domain.rhyme_rules import rhyme_key
from app.models.token import Token
from app.schemas.draft_analysis import (
    DraftAnalysisRequest,
    DraftAnalysisResponse,
    DraftDetail,
    DraftSummary,
    Insight,
    RepetitionSignal,
    SectionAnalysis,
)
from app.services.draft_nlp_service import DraftNlpService
from app.services.language_router import LanguageContext


_logger = get_logger("nlp.draft_analysis")


# Chorus and hook labels where opening repetition is presumed intentional.
_HOOK_LABELS: frozenset[str] = frozenset({"chorus", "hook", "refrain"})
# Word-overuse severity escalates from medium to high at this line count.
_OVERUSE_HIGH = 5


# Per-request cache of rhyme keys, keyed on the last token's identifying word.
RhymeCache = dict[str, str | None]


@dataclass(frozen=True, slots=True)
class _SectionResult:
    payload: SectionAnalysis
    insights: list[Insight]
    notable: str | None
    token_lists: list[list[str]]
    token_objects: list[list[Token]]


# Map an insight type to a coarse family bucket for the summary's
# family_counts. UI uses these to stage complexity.
_FAMILY_FOR_TYPE: dict[str, str] = {
    "syllable_variance": "cadence",
    "repetition_opening": "repetition",
    "repetition_ending": "repetition",
    "word_overuse": "repetition",
    "semantic_repetition": "semantic",
    "motif_concentration": "motif",
    "section_contrast": "contrast",
    "perspective_drift": "consistency",
    "tense_drift": "consistency",
}


class DraftAnalysisService:
    """Stateless orchestrator. One instance per app, dispatched per request."""

    def __init__(self, nlp_service: DraftNlpService | None = None) -> None:
        self._nlp_service = nlp_service

    def analyze(
        self,
        request: DraftAnalysisRequest,
        context: LanguageContext,
    ) -> DraftAnalysisResponse:
        explicit = (
            [(s.id, s.label, s.line_start, s.line_end) for s in request.sections]
            if request.sections
            else None
        )
        with timed(
            _logger,
            "analyze_draft.parse_sections",
            language=request.language,
            chars=len(request.content),
        ):
            parsed = parse_sections(request.content, explicit)

        sections_by_id = {s.id: s for s in parsed}

        section_payloads: list[SectionAnalysis] = []
        insights: list[Insight] = []
        notable_patterns: list[str] = []
        total_lines = 0
        total_syllables = 0
        all_token_lists: list[list[str]] = []
        section_tokens: dict[str, list[list[Token]]] = {}
        # (global 1-based line number, tokens) for inner-rhyme detection.
        inner_rhyme_lines: list[tuple[int, list[Token]]] = []
        rhyme_cache: RhymeCache = {}

        with timed(
            _logger,
            "analyze_draft.per_section_pipeline",
            language=request.language,
            sections=len(parsed),
        ):
            for section in parsed:
                result = self._analyze_section(context, section, rhyme_cache)
                section_payloads.append(result.payload)
                insights.extend(result.insights)
                if result.notable is not None:
                    notable_patterns.append(result.notable)
                total_lines += result.payload.line_count
                total_syllables += sum(result.payload.syllable_pattern)
                all_token_lists.extend(result.token_lists)
                section_tokens[section.id] = result.token_objects
                for offset, line_tokens in enumerate(result.token_objects):
                    inner_rhyme_lines.append(
                        (section.line_start + offset, line_tokens)
                    )

        with timed(
            _logger,
            "analyze_draft.draft_overuse",
            lines=len(all_token_lists),
        ):
            insights.extend(self._build_overuse_insights(all_token_lists))

        capabilities = base_capabilities(request.language)
        motifs: list[str] = []
        hook_only_overuse: frozenset[str] = frozenset()
        opts = request.options
        wants_semantic = opts is not None and opts.include_semantic_repetition
        wants_motif = opts is not None and opts.include_motif_tracking
        wants_contrast = opts is not None and opts.include_section_contrast
        wants_consistency = opts is not None and opts.include_consistency_hints
        if (
            wants_semantic
            or wants_motif
            or wants_contrast
            or wants_consistency
        ) and self._nlp_service is not None:
            if self._nlp_service.supports(request.language):
                with timed(
                    _logger,
                    "analyze_draft.semantic_pipeline",
                    language=request.language,
                ):
                    nlp_result = self._nlp_service.analyze(
                        language=request.language,
                        sections=parsed,
                        line_token_objects=section_tokens,
                        include_semantic_repetition=wants_semantic,
                        include_motif_tracking=wants_motif,
                        include_section_contrast=wants_contrast,
                        include_consistency_hints=wants_consistency,
                    )
                if wants_semantic:
                    capabilities.semantic_repetition = opt_in_capability("full")
                    for sem in nlp_result.semantic_repetition:
                        insights.append(
                            build_semantic_repetition_insight(sem, sections_by_id)
                        )
                if wants_motif:
                    capabilities.motif_tracking = opt_in_capability("full")
                    motifs = list(nlp_result.motifs)
                    for mot in nlp_result.motif_insights:
                        insights.append(
                            build_motif_insight(mot, sections_by_id)
                        )
                if wants_contrast:
                    capabilities.section_contrast = opt_in_capability("full")
                    for con in nlp_result.section_contrast:
                        insights.append(build_section_contrast_insight(con))
                if wants_consistency:
                    capabilities.consistency_hints = opt_in_capability(
                        nlp_result.consistency_capability or "unsupported"
                    )
                    for cdr in nlp_result.consistency:
                        insights.append(
                            build_consistency_insight(cdr, sections_by_id)
                        )
                hook_only_overuse = nlp_result.hook_only_overuse_words

        # Final pass: demote intentional-repetition signals inside hook
        # sections so the response speaks the writer's intent.
        insights = demote_inside_hooks(insights, parsed, hook_only_overuse)

        with timed(
            _logger,
            "analyze_draft.inner_rhymes",
            lines=len(inner_rhyme_lines),
        ):
            phoneme_cache: dict[str, tuple[str, ...] | None] = {}
            inner_rhymes = find_inner_rhyme_groups(
                inner_rhyme_lines,
                phonemes_for_context(context, phoneme_cache),
                request.language,
            )

        return DraftAnalysisResponse(
            language=request.language,
            title=request.title,
            capabilities=capabilities,
            summary=self._build_summary(
                section_payloads,
                total_lines,
                total_syllables,
                notable_patterns,
                motifs,
                insights,
            ),
            insights=insights,
            detail=DraftDetail(sections=section_payloads),
            inner_rhymes=inner_rhymes,
        )

    def _analyze_section(
        self,
        ctx: LanguageContext,
        section: ParsedSection,
        rhyme_cache: RhymeCache,
    ) -> _SectionResult:
        line_token_objects: list[list[Token]] = [
            ctx.engine.tokenize_line(line.text) for line in section.lines
        ]
        line_token_lists: list[list[str]] = [
            [t.normalized for t in tokens] for tokens in line_token_objects
        ]
        syllable_pattern = [
            self._line_syllables(ctx, tokens) for tokens in line_token_objects
        ]
        keys = [
            self._line_rhyme_key(ctx, tokens, rhyme_cache)
            for tokens in line_token_objects
        ]
        scheme, confidence = assign_scheme(keys)
        cadence = classify_pattern(syllable_pattern, section.label)

        rep_domain = detect_section_signals(line_token_lists)
        rep_signals = [
            RepetitionSignal(type=s.type, value=s.value) for s in rep_domain
        ]

        payload = SectionAnalysis(
            id=section.id,
            label=section.label,
            line_start=section.line_start,
            line_end=section.line_end,
            line_count=len(section.lines),
            rhyme_scheme=scheme,
            rhyme_scheme_confidence=confidence,
            syllable_pattern=syllable_pattern,
            syllable_variance=cadence.variance,
            cadence_class=cadence.cadence_class,
            repetition_signals=rep_signals,
        )

        insights: list[Insight] = []
        notable: str | None = None
        if section.lines:
            insights.append(
                build_syllable_variance_insight(
                    section,
                    variance=cadence.variance,
                    cadence_class=cadence.cadence_class,
                    severity=cadence.severity,
                    message=cadence.message,
                )
            )
            insights.extend(
                _repetition_insights(section, rep_domain)
            )
            if cadence.cadence_class == "consistent" and len(syllable_pattern) >= 2:
                notable = _notable_consistency(section)

        return _SectionResult(
            payload=payload,
            insights=insights,
            notable=notable,
            token_lists=line_token_lists,
            token_objects=line_token_objects,
        )

    def _build_overuse_insights(
        self, all_token_lists: list[list[str]]
    ) -> list[Insight]:
        out: list[Insight] = []
        for overuse in detect_draft_overuse(all_token_lists):
            severity = "high" if overuse.line_count >= _OVERUSE_HIGH else "medium"
            out.append(
                build_word_overuse_insight(
                    word=overuse.word,
                    line_count=overuse.line_count,
                    severity=severity,
                    message=(
                        f'"{overuse.word}" appears on {overuse.line_count} lines.'
                    ),
                )
            )
        return out

    def _build_summary(
        self,
        section_payloads: list[SectionAnalysis],
        total_lines: int,
        total_syllables: int,
        notable_patterns: list[str],
        motifs: list[str] | None,
        insights: list[Insight],
    ) -> DraftSummary:
        counts: Counter[str] = Counter()
        for ins in insights:
            family = _FAMILY_FOR_TYPE.get(ins.type)
            if family:
                counts[family] += 1
        return DraftSummary(
            section_count=len(section_payloads),
            line_count=total_lines,
            total_syllables=total_syllables,
            notable_patterns=notable_patterns,
            motifs=motifs or [],
            insight_count=len(insights),
            family_counts=dict(counts),
        )

    def _line_syllables(self, ctx: LanguageContext, tokens: list[Token]) -> int:
        if not tokens:
            return 0
        total, _ = ctx.syllable_service.count_tokens(tokens)
        return total

    def _line_rhyme_key(
        self,
        ctx: LanguageContext,
        tokens: list[Token],
        cache: RhymeCache,
    ) -> str | None:
        if not tokens:
            return None
        last = tokens[-1]
        if ctx.engine.code == "en":
            cache_key = f"en:{last.text}"
            if cache_key in cache:
                return cache[cache_key]
            key = _english_rhyme_key(ctx, last.text, last.normalized)
            cache[cache_key] = key
            return key
        if ctx.engine.code == "es":
            cache_key = f"es:{last.normalized}"
            if cache_key in cache:
                return cache[cache_key]
            key = _spanish_rhyme_key(last.normalized)
            cache[cache_key] = key
            return key
        return None


def _english_rhyme_key(
    ctx: LanguageContext, text: str, normalized: str
) -> str | None:
    _, prons = ctx.pronunciation_service.lookup(text)
    if prons and prons[0].phonemes:
        key = rhyme_key(prons[0].phonemes)
        if key is not None:
            return key
    if not normalized:
        return None
    tails = heuristic_phoneme_tails(normalized)
    if not tails:
        return None
    return rhyme_key(tails[0])


def _spanish_rhyme_key(normalized: str | None) -> str | None:
    if not normalized:
        return None
    pron = spanish_g2p(normalized)
    if not pron.phonemes:
        return None
    return consonant_rhyme_key(pron.phonemes)


def _repetition_insights(
    section: ParsedSection,
    signals: list[DomainRepetitionSignal],
) -> list[Insight]:
    if not signals:
        return []
    is_hook = section.label in _HOOK_LABELS
    out: list[Insight] = []
    for sig in signals:
        if sig.type == "opening_phrase_repeat":
            severity = "info" if is_hook else "low"
            out.append(
                build_repetition_opening_insight(
                    section,
                    phrase=sig.value,
                    severity=severity,
                    message=f'Lines open with "{sig.value}".',
                )
            )
        elif sig.type == "ending_word_repeat":
            out.append(
                build_repetition_ending_insight(
                    section,
                    word=sig.value,
                    severity="info",
                    message=f'Multiple lines close with "{sig.value}".',
                )
            )
    return out


def _notable_consistency(section: ParsedSection) -> str:
    where = section.label or "Section"
    return f"{where.capitalize()} line lengths are closely matched."


__all__ = ["DraftAnalysisService"]
