"""Spanish word normalization.

Mirrors the English module's contract (lowercase + strip outer punctuation +
flatten curly quotes) but preserves Spanish-specific characters: ñ, the
accented vowels á é í ó ú, and ü. It also strips the inverted punctuation
``¿`` / ``¡`` that English does not need to handle.
"""

from __future__ import annotations

import re

# Narrow set of common Spanish lyric contractions/elisions. ``del`` and ``al``
# are obligatory contractions in modern Spanish; the rest are common in lyrics
# and informal speech. Kept narrow to avoid expanding words that look like
# contractions but aren't (e.g. ``pa`` standing alone is ambiguous — only the
# apostrophised ``pa'`` is rewritten).
_CONTRACTIONS: dict[str, str] = {
    "del": "de el",
    "al": "a el",
    "pa'": "para",
    "p'": "para",
    "na'": "nada",
    "to'": "todo",
    "tó": "todo",
}

# Accepts a leading letter, then optional letters, apostrophes, or hyphens,
# closing on a letter. Includes ñ, accented vowels, and ü.
_WORD_RE = re.compile(r"^[a-záéíóúñü][a-záéíóúñü'\-]*[a-záéíóúñü]?$")
_PUNCT_STRIP = "\"'.,;:!?¡¿()[]{}<>—–"


def _flatten_quotes(text: str) -> str:
    return (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def normalize_word(text: str | None) -> str | None:
    """Lowercase, strip surrounding punctuation, collapse curly quotes.

    Returns None for empty input or anything that is not a recognizable
    Spanish word. Accents and ñ pass through unchanged so downstream
    syllabification can use them as stress markers.
    """
    if not text:
        return None
    cleaned = _flatten_quotes(text).strip().strip(_PUNCT_STRIP).lower()
    if not cleaned:
        return None
    if not _WORD_RE.match(cleaned):
        return None
    return cleaned


def expand_basic_contractions(text: str) -> str:
    """Replace known Spanish contractions/elisions, case-insensitive."""
    if not text:
        return text
    tokens = text.split()
    out: list[str] = []
    for tok in tokens:
        key = _flatten_quotes(tok).lower()
        stripped = key.strip(_PUNCT_STRIP)
        # Try the punctuation-stripped form first, then re-add a trailing
        # apostrophe so ``pa'`` matches its dictionary entry even after
        # outer punctuation has been removed.
        if stripped in _CONTRACTIONS:
            out.append(_CONTRACTIONS[stripped])
        elif (stripped + "'") in _CONTRACTIONS:
            out.append(_CONTRACTIONS[stripped + "'"])
        elif key in _CONTRACTIONS:
            out.append(_CONTRACTIONS[key])
        else:
            out.append(tok)
    return " ".join(out)
