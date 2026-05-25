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
            word = _extract_overuse_word(insight.message)
            if word and word in hook_words:
                should_demote = True
        if not should_demote:
            out.append(insight)
            continue
        new_severity = _SEVERITY_DEMOTION.get(insight.severity, insight.severity)
        evidence = dict(insight.evidence) if insight.evidence else {}
        evidence["hook_context"] = True
        out.append(
            insight.model_copy(
                update={"severity": new_severity, "evidence": evidence}
            )
        )
    return out


def _extract_overuse_word(message: str) -> str | None:
    # word_overuse messages have the shape: "\"word\" appears on N lines."
    if not message or '"' not in message:
        return None
    first = message.find('"')
    second = message.find('"', first + 1)
    if first < 0 or second < 0:
        return None
    return message[first + 1 : second]


__all__ = ["demote_inside_hooks"]
