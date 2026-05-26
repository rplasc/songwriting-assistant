"""Repetition delta rules.

Diffs per-section ``repetition_signals`` (opening_phrase_repeat /
ending_word_repeat) across matched section pairs. Anchors compare
insights to the **current** section so the UI can jump to the new
state.
"""

from __future__ import annotations

from app.domain.draft_compare._compare_insight import (
    build_compare_insight,
    section_anchor,
)
from app.domain.draft_compare.section_matcher import SectionMatchResult
from app.schemas.draft_analysis import Insight, SectionAnalysis
from app.schemas.evidence import (
    RepetitionSignalAddedEvidence,
    RepetitionSignalRemovedEvidence,
)


def _signal_set(section: SectionAnalysis) -> set[tuple[str, str]]:
    return {(s.type, s.value) for s in section.repetition_signals}


def compute_repetition_deltas(match: SectionMatchResult) -> list[Insight]:
    out: list[Insight] = []
    for prev_s, cur_s in match.pairs:
        prev_set = _signal_set(prev_s)
        cur_set = _signal_set(cur_s)
        added = sorted(cur_set - prev_set)
        removed = sorted(prev_set - cur_set)
        for signal_type, value in added:
            out.append(
                build_compare_insight(
                    insight_type="repetition_signal_added",
                    scope="section",
                    target=cur_s.id,
                    severity="info",
                    message=(
                        f'New {signal_type} signal "{value}" '
                        f"in {cur_s.label or 'this section'}."
                    ),
                    evidence=RepetitionSignalAddedEvidence(
                        signal_type=signal_type,
                        value=value,
                        section_id=cur_s.id,
                    ),
                    anchor=section_anchor(cur_s),
                )
            )
        for signal_type, value in removed:
            out.append(
                build_compare_insight(
                    insight_type="repetition_signal_removed",
                    scope="section",
                    target=cur_s.id,
                    severity="info",
                    message=(
                        f'{signal_type.capitalize()} signal "{value}" '
                        f"is gone from {cur_s.label or 'this section'}."
                    ),
                    evidence=RepetitionSignalRemovedEvidence(
                        signal_type=signal_type,
                        value=value,
                        section_id=cur_s.id,
                    ),
                    anchor=section_anchor(cur_s),
                )
            )
    return out


__all__ = ["compute_repetition_deltas"]
