"""Downgrade severity on insights inside chorus/hook/refrain sections.

Intentional repetition in a hook is a feature, not a defect. After all
insights are assembled, this pass walks the list once and demotes
severity on a fixed set of insight types whose ``target`` lands inside
a hook-labeled section. ``word_overuse`` is special-cased: it's
``scope="draft"`` (no per-section target), so it only gets demoted
when *every* line where the word appears is inside a hook section —
the caller supplies that mapping.
"""

from __future__ import annotations

from app.domain.draft_analysis.section_parser import ParsedSection
from app.schemas.draft_analysis import Insight
from app.schemas.evidence import WordOveruseEvidence

_HOOK_LABELS: frozenset[str] = frozenset({"chorus", "hook", "refrain"})
_DEMOTABLE_TYPES: frozenset[str] = frozenset(
    {"semantic_repetition", "repetition_ending", "word_overuse"}
)

_SEVERITY_DEMOTION: dict[str, str] = {
    "high": "medium",
    "medium": "low",
    "low": "info",
}


def demote_inside_hooks(
    insights: list[Insight],
    sections: list[ParsedSection],
    hook_only_overuse_words: frozenset[str] | None = None,
) -> list[Insight]:
    """Return a new list with hook-scoped insights demoted.

    ``hook_only_overuse_words`` is the set of overused-word lemmas whose
    appearances are entirely confined to hook-labeled sections. When
    provided, ``word_overuse`` insights for those words are demoted too.
    """
    hook_ids = {s.id for s in sections if s.label in _HOOK_LABELS}
    hook_words = hook_only_overuse_words or frozenset()
    out: list[Insight] = []
    for insight in insights:
        if insight.type not in _DEMOTABLE_TYPES:
            out.append(insight)
            continue
        should_demote = False
        if insight.scope == "section" and insight.target in hook_ids:
            should_demote = True
        elif insight.type == "word_overuse" and insight.scope == "draft":
            word = (
                insight.evidence.word
                if isinstance(insight.evidence, WordOveruseEvidence)
                else None
            )
            if word and word in hook_words:
                should_demote = True
        if not should_demote:
            out.append(insight)
            continue
        new_severity = _SEVERITY_DEMOTION.get(insight.severity, insight.severity)
        out.append(
            insight.model_copy(
                update={"severity": new_severity, "hook_context": True}
            )
        )
    return out


__all__ = ["demote_inside_hooks"]
