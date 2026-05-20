"""Detect repetition signals within sections and across a full draft.

Phase 4 Milestone 3. All analysis is token-based so the same rules work for
both English and Spanish without language-specific branching.

Three categories:

1. Opening-phrase repeat (anaphora) — 2+ lines in a section share the same
   normalized starting word(s).  This is typically intentional in a chorus
   and may be accidental elsewhere; severity reflects that distinction.

2. Ending-word repeat — 2+ lines in a section close with the same normalized
   word.  Complements the rhyme scheme: the scheme shows the *pattern*; this
   flags the exact *word* reuse, which can strengthen or weaken a section
   depending on intent.

3. Draft-level word overuse — a content word appears on many distinct lines
   across the whole draft.  Stop-word filtering prevents common function words
   from drowning out real signal.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Stop-word filter ──────────────────────────────────────────────────────────
# Covers the most common English and Spanish function words.  The list is
# intentionally lean — over-filtering would hide genuine repetition.
_STOP_WORDS: frozenset[str] = frozenset(
    {
        # English
        "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
        "they", "them", "their", "his", "her", "its",
        "a", "an", "the",
        "and", "but", "or", "nor", "so", "yet", "for",
        "in", "on", "at", "to", "of", "by", "up", "as", "if",
        "is", "are", "was", "were", "be", "been", "am",
        "have", "has", "had", "do", "did", "does",
        "that", "this", "these", "those", "with", "from", "not", "no",
        "all", "can", "will", "just", "about", "into", "then", "when",
        "there", "what", "how", "who", "which", "where",
        # Spanish
        "yo", "tu", "el", "ella", "nosotros", "vosotros", "ellos", "ellas",
        "me", "te", "se", "nos", "les",
        "un", "una", "unos", "unas", "lo", "la", "los", "las",
        "y", "e", "o", "u", "pero", "sino", "ni", "que",
        "en", "de", "a", "por", "para", "con", "sin", "sobre", "bajo",
        "es", "son", "era", "fue", "ser", "estar", "hay",
        "no", "si", "ya", "mas", "tan", "muy",
        "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
        "que", "como", "cuando", "donde", "quien", "cual",
    }
)

_MAX_PREFIX_TOKENS = 5
# Minimum lines that must share a prefix or closing word to be reported.
_MIN_REPEAT_LINES = 2
# Minimum distinct lines a word must appear on to be flagged as overuse.
_OVERUSE_THRESHOLD = 3


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RepetitionSignal:
    type: str   # "opening_phrase_repeat" | "ending_word_repeat"
    value: str  # the shared phrase or word


@dataclass(frozen=True, slots=True)
class OveruseSignal:
    word: str
    line_count: int  # number of distinct lines the word appears on


# ── Section-level detection ───────────────────────────────────────────────────

def detect_section_signals(token_lists: list[list[str]]) -> list[RepetitionSignal]:
    """Detect opening-phrase and ending-word repeats within one section.

    ``token_lists`` is one entry per lyric line, each entry being the
    pre-normalized tokens for that line.  Blank / empty lines are skipped
    by the caller (they should not appear here).
    """
    non_empty = [tl for tl in token_lists if tl]
    if len(non_empty) < _MIN_REPEAT_LINES:
        return []

    signals: list[RepetitionSignal] = []
    signals.extend(_opening_phrase_signals(non_empty))
    signals.extend(_ending_word_signals(non_empty))
    return signals


def _opening_phrase_signals(token_lists: list[list[str]]) -> list[RepetitionSignal]:
    """Find the longest shared opening prefix across groups of 2+ lines."""
    # Group line indices by first token.
    from collections import defaultdict
    by_first: dict[str, list[int]] = defaultdict(list)
    for idx, tl in enumerate(token_lists):
        by_first[tl[0]].append(idx)

    signals: list[RepetitionSignal] = []
    for _first_tok, indices in by_first.items():
        if len(indices) < _MIN_REPEAT_LINES:
            continue
        group = [token_lists[i] for i in indices]
        prefix = _longest_common_prefix(group, _MAX_PREFIX_TOKENS)
        if not prefix:
            continue
        signals.append(
            RepetitionSignal(
                type="opening_phrase_repeat",
                value=" ".join(prefix),
            )
        )
    return signals


def _ending_word_signals(token_lists: list[list[str]]) -> list[RepetitionSignal]:
    from collections import defaultdict
    by_last: dict[str, int] = defaultdict(int)
    for tl in token_lists:
        by_last[tl[-1]] += 1

    return [
        RepetitionSignal(type="ending_word_repeat", value=word)
        for word, count in by_last.items()
        if count >= _MIN_REPEAT_LINES
    ]


def _longest_common_prefix(
    token_lists: list[list[str]], max_len: int
) -> list[str]:
    """Return the longest common leading token sequence across all lists."""
    if not token_lists:
        return []
    prefix: list[str] = []
    for pos in range(min(max_len, min(len(tl) for tl in token_lists))):
        tok = token_lists[0][pos]
        if all(tl[pos] == tok for tl in token_lists[1:]):
            prefix.append(tok)
        else:
            break
    return prefix


# ── Draft-level overuse detection ────────────────────────────────────────────

def detect_draft_overuse(all_token_lists: list[list[str]]) -> list[OveruseSignal]:
    """Find content words that appear on many distinct lyric lines.

    ``all_token_lists`` is a flat list of per-line token lists spanning the
    entire draft (all sections combined).

    Returns signals sorted by line_count descending so the most-repeated
    words come first.
    """
    # Count distinct lines each word appears on (not total occurrences).
    word_lines: dict[str, set[int]] = {}
    for line_idx, tokens in enumerate(all_token_lists):
        for tok in tokens:
            if tok in _STOP_WORDS or len(tok) < 2:
                continue
            if tok not in word_lines:
                word_lines[tok] = set()
            word_lines[tok].add(line_idx)

    signals = [
        OveruseSignal(word=word, line_count=len(lines))
        for word, lines in word_lines.items()
        if len(lines) >= _OVERUSE_THRESHOLD
    ]
    signals.sort(key=lambda s: s.line_count, reverse=True)
    return signals


__all__ = [
    "RepetitionSignal",
    "OveruseSignal",
    "detect_section_signals",
    "detect_draft_overuse",
]
