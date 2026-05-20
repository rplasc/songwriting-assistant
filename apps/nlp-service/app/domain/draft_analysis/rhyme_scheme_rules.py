"""Map per-line rhyme keys to a scheme string like ``"ABAB"``.

A ``None`` key means the line's last-word rhyme could not be resolved
(e.g. unknown token, no vowel). It is rendered as ``"?"`` and downgrades
the section's confidence to ``"partial"``.

Letters reuse in order of first appearance: the first key becomes A, the
next distinct key becomes B, and so on. With more than 26 distinct keys
(unusual for a single section) we keep cycling A-Z; consumers should
treat the string as opaque past that point.
"""

from __future__ import annotations

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def assign_scheme(keys: list[str | None]) -> tuple[str, str]:
    """Return (scheme_letters, confidence).

    Empty input returns ``("", "full")``.
    """
    if not keys:
        return "", "full"

    letter_by_key: dict[str, str] = {}
    out: list[str] = []
    confidence = "full"
    next_letter = 0
    for key in keys:
        if key is None:
            out.append("?")
            confidence = "partial"
            continue
        letter = letter_by_key.get(key)
        if letter is None:
            letter = _ALPHABET[next_letter % len(_ALPHABET)]
            letter_by_key[key] = letter
            next_letter += 1
        out.append(letter)
    return "".join(out), confidence


__all__ = ["assign_scheme"]
