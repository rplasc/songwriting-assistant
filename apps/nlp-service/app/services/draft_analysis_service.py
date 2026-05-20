"""Compose line-level primitives into draft-level analysis.

Phase 4 Milestones 1-2: section parsing, rhyme-scheme assignment, and
syllable-pattern cadence classification. Repetition and stress-hint
insights are deferred and reported as ``unsupported`` capabilities.
"""

from __future__ import annotations

from app.domain.draft_analysis.cadence_rules import (
    CadenceSummary,
    classify_pattern,
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
from app.schemas.draft_analysis import (
    Capabilities,
    DraftAnalysisRequest,
    DraftAnalysisResponse,
    DraftSummary,
    Insight,
    SectionAnalysis,
)
from app.services.language_router import LanguageContext


_BASE_CAPABILITIES: dict[str, Capabilities] = {
    "en": Capabilities(
        rhyme_scheme="full",
        cadence_patterns="full",
        stress_hints="unsupported",
        repetition="unsupported",
        mixed_language="unsupported",
    ),
    "es": Capabilities(
        rhyme_scheme="full",
        cadence_patterns="full",
        stress_hints="unsupported",
        repetition="unsupported",
        mixed_language="unsupported",
    ),
}


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
        parsed = parse_sections(request.content, explicit)

        section_payloads: list[SectionAnalysis] = []
        insights: list[Insight] = []
        notable_patterns: list[str] = []
        total_lines = 0
        total_syllables = 0

        for section in parsed:
            syllable_pattern = [
                self._line_syllables(context, line.text) for line in section.lines
            ]
            keys = [
                self._line_rhyme_key(context, line.text) for line in section.lines
            ]
            scheme, confidence = assign_scheme(keys)
            cadence = classify_pattern(syllable_pattern, section.label)

            section_payloads.append(
                SectionAnalysis(
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
                    repetition_signals=[],
                )
            )

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
                if cadence.cadence_class == "consistent" and len(syllable_pattern) >= 2:
                    notable_patterns.append(_notable_consistency(section, cadence))

            total_lines += len(section.lines)
            total_syllables += sum(syllable_pattern)

        return DraftAnalysisResponse(
            language=request.language,
            title=request.title,
            capabilities=_BASE_CAPABILITIES[request.language],
            summary=DraftSummary(
                section_count=len(section_payloads),
                line_count=total_lines,
                total_syllables=total_syllables,
                notable_patterns=notable_patterns,
            ),
            sections=section_payloads,
            insights=insights,
        )

    def _line_syllables(self, ctx: LanguageContext, line_text: str) -> int:
        if not line_text:
            return 0
        tokens = ctx.engine.tokenize_line(line_text)
        if not tokens:
            return 0
        total, _ = ctx.syllable_service.count_tokens(tokens)
        return total

    def _line_rhyme_key(self, ctx: LanguageContext, line_text: str) -> str | None:
        tokens = ctx.engine.tokenize_line(line_text)
        if not tokens:
            return None
        last = tokens[-1]
        if ctx.engine.code == "en":
            return _english_rhyme_key(ctx, last.text, last.normalized)
        if ctx.engine.code == "es":
            return _spanish_rhyme_key(last.normalized)
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


def _notable_consistency(section: ParsedSection, cadence: CadenceSummary) -> str:
    where = section.label or "Section"
    return f"{where.capitalize()} line lengths are closely matched."


__all__ = ["DraftAnalysisService"]
