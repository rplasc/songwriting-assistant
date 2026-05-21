"""Compose line-level primitives into draft-level analysis.

Current Phase: section parsing, rhyme-scheme assignment,
syllable-pattern cadence classification, and repetition detection.
Stress-hint insights remain deferred.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger, timed
from app.domain.draft_analysis.cadence_rules import classify_pattern
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
from app.domain.rhyme_rules import rhyme_key
from app.models.token import Token
from app.schemas.draft_analysis import (
    Capabilities,
    DraftAnalysisRequest,
    DraftAnalysisResponse,
    DraftSummary,
    Insight,
    RepetitionSignal,
    SectionAnalysis,
)
from app.services.language_router import LanguageContext


_logger = get_logger("nlp.draft_analysis")


_BASE_CAPABILITIES: dict[str, Capabilities] = {
    "en": Capabilities(
        rhyme_scheme="full",
        cadence_patterns="full",
        stress_hints="unsupported",
        repetition="full",
        mixed_language="unsupported",
    ),
    "es": Capabilities(
        rhyme_scheme="full",
        cadence_patterns="full",
        stress_hints="unsupported",
        repetition="full",
        mixed_language="unsupported",
    ),
}

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


class DraftAnalysisService:
    """Stateless orchestrator. One instance per app, dispatched per request."""

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

        section_payloads: list[SectionAnalysis] = []
        insights: list[Insight] = []
        notable_patterns: list[str] = []
        total_lines = 0
        total_syllables = 0
        all_token_lists: list[list[str]] = []
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

        with timed(
            _logger,
            "analyze_draft.draft_overuse",
            lines=len(all_token_lists),
        ):
            insights.extend(self._build_overuse_insights(all_token_lists))

        return DraftAnalysisResponse(
            language=request.language,
            title=request.title,
            capabilities=_BASE_CAPABILITIES[request.language],
            summary=self._build_summary(
                section_payloads, total_lines, total_syllables, notable_patterns
            ),
            sections=section_payloads,
            insights=insights,
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
                Insight(
                    type="syllable_variance",
                    scope="section",
                    target=section.id,
                    severity=cadence.severity,
                    message=cadence.message,
                )
            )
            insights.extend(
                _repetition_insights(section.id, section.label, rep_domain)
            )
            if cadence.cadence_class == "consistent" and len(syllable_pattern) >= 2:
                notable = _notable_consistency(section)

        return _SectionResult(
            payload=payload,
            insights=insights,
            notable=notable,
            token_lists=line_token_lists,
        )

    def _build_overuse_insights(
        self, all_token_lists: list[list[str]]
    ) -> list[Insight]:
        out: list[Insight] = []
        for overuse in detect_draft_overuse(all_token_lists):
            severity = "high" if overuse.line_count >= _OVERUSE_HIGH else "medium"
            out.append(
                Insight(
                    type="word_overuse",
                    scope="draft",
                    target=None,
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
    ) -> DraftSummary:
        return DraftSummary(
            section_count=len(section_payloads),
            line_count=total_lines,
            total_syllables=total_syllables,
            notable_patterns=notable_patterns,
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
    section_id: str,
    label: str | None,
    signals: list[DomainRepetitionSignal],
) -> list[Insight]:
    if not signals:
        return []
    is_hook = label in _HOOK_LABELS
    out: list[Insight] = []
    for sig in signals:
        if sig.type == "opening_phrase_repeat":
            # Anaphora in a chorus/hook label is almost always intentional.
            severity = "info" if is_hook else "low"
            out.append(
                Insight(
                    type="repetition_opening",
                    scope="section",
                    target=section_id,
                    severity=severity,
                    message=f'Lines open with "{sig.value}".',
                )
            )
        elif sig.type == "ending_word_repeat":
            out.append(
                Insight(
                    type="repetition_ending",
                    scope="section",
                    target=section_id,
                    severity="info",
                    message=f'Multiple lines close with "{sig.value}".',
                )
            )
    return out


def _notable_consistency(section: ParsedSection) -> str:
    where = section.label or "Section"
    return f"{where.capitalize()} line lengths are closely matched."


__all__ = ["DraftAnalysisService"]
