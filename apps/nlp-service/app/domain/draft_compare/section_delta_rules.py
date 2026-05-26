"""Section-level shape deltas.

For each matched section pair: rhyme scheme shift, cadence-class shift,
and syllable-pattern shift. The syllable-pattern rule suppresses tiny
single-line drifts by only emitting when the maximum absolute delta
exceeds a small threshold.
"""

from __future__ import annotations

from app.domain.draft_compare._compare_insight import (
    build_compare_insight,
    section_anchor,
)
from app.domain.draft_compare.section_matcher import SectionMatchResult
from app.schemas.draft_analysis import Insight, SectionAnalysis
from app.schemas.evidence import (
    SectionCadenceShiftEvidence,
    SectionRhymeSchemeShiftEvidence,
    SectionSyllablePatternShiftEvidence,
)

_SYLLABLE_PATTERN_NOISE_THRESHOLD = 2  # ignore single-syllable wobble


def _rhyme_shift_insight(
    prev_s: SectionAnalysis, cur_s: SectionAnalysis
) -> Insight | None:
    if prev_s.rhyme_scheme == cur_s.rhyme_scheme:
        return None
    return build_compare_insight(
        insight_type="section_rhyme_scheme_shift",
        scope="section",
        target=cur_s.id,
        severity="low",
        message=(
            f"Rhyme scheme moved from {prev_s.rhyme_scheme} "
            f"to {cur_s.rhyme_scheme}."
        ),
        evidence=SectionRhymeSchemeShiftEvidence(
            section_id=cur_s.id,
            previous=prev_s.rhyme_scheme,
            current=cur_s.rhyme_scheme,
        ),
        anchor=section_anchor(cur_s),
        confidence="medium",
    )


def _cadence_shift_insight(
    prev_s: SectionAnalysis, cur_s: SectionAnalysis
) -> Insight | None:
    if prev_s.cadence_class == cur_s.cadence_class:
        return None
    return build_compare_insight(
        insight_type="section_cadence_shift",
        scope="section",
        target=cur_s.id,
        severity="info",
        message=(
            f"Cadence moved from {prev_s.cadence_class} "
            f"to {cur_s.cadence_class}."
        ),
        evidence=SectionCadenceShiftEvidence(
            section_id=cur_s.id,
            previous=prev_s.cadence_class,
            current=cur_s.cadence_class,
        ),
        anchor=section_anchor(cur_s),
        confidence="medium",
    )


def _syllable_pattern_shift_insight(
    prev_s: SectionAnalysis, cur_s: SectionAnalysis
) -> Insight | None:
    prev_pat = prev_s.syllable_pattern
    cur_pat = cur_s.syllable_pattern
    if len(prev_pat) != len(cur_pat):
        # Length change is an editorial event — emit a shift, deltas filled
        # by padding the shorter side with zeros so the field stays typed.
        max_len = max(len(prev_pat), len(cur_pat))
        prev_pad = prev_pat + [0] * (max_len - len(prev_pat))
        cur_pad = cur_pat + [0] * (max_len - len(cur_pat))
        delta = [c - p for p, c in zip(prev_pad, cur_pad)]
        if max(abs(d) for d in delta) < _SYLLABLE_PATTERN_NOISE_THRESHOLD:
            return None
        return build_compare_insight(
            insight_type="section_syllable_pattern_shift",
            scope="section",
            target=cur_s.id,
            severity="info",
            message="Line count changed in this section.",
            evidence=SectionSyllablePatternShiftEvidence(
                section_id=cur_s.id,
                previous=prev_pat,
                current=cur_pat,
                delta=delta,
            ),
            anchor=section_anchor(cur_s),
            confidence="medium",
        )
    delta = [c - p for p, c in zip(prev_pat, cur_pat)]
    if not delta or max(abs(d) for d in delta) < _SYLLABLE_PATTERN_NOISE_THRESHOLD:
        return None
    return build_compare_insight(
        insight_type="section_syllable_pattern_shift",
        scope="section",
        target=cur_s.id,
        severity="info",
        message="Syllable pattern shifted in this section.",
        evidence=SectionSyllablePatternShiftEvidence(
            section_id=cur_s.id,
            previous=prev_pat,
            current=cur_pat,
            delta=delta,
        ),
        anchor=section_anchor(cur_s),
        confidence="low",
    )


def compute_section_deltas(match: SectionMatchResult) -> list[Insight]:
    out: list[Insight] = []
    for prev_s, cur_s in match.pairs:
        for builder in (
            _rhyme_shift_insight,
            _cadence_shift_insight,
            _syllable_pattern_shift_insight,
        ):
            ins = builder(prev_s, cur_s)
            if ins is not None:
                out.append(ins)
    return out


__all__ = ["compute_section_deltas"]
