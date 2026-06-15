"""Map per-line rhyme keys to a scheme string like ``"ABAB"``.

Each line may carry more than one candidate key (heteronyms like "read" or
"live" resolve to a key per pronunciation, unknown words to a key per
heuristic tail). Two lines are assigned the same letter if *any* of their
keys match, and this matching is transitive: if line A shares a key with line
B, and line B (via a different key) shares one with line C, all three get the
same letter even if A and C share nothing directly.

A line with no resolvable key — ``None``, an empty set, or empty string — is
rendered as ``"?"`` and downgrades the section's confidence to ``"partial"``.

Letters are assigned in order of first appearance: the first group becomes A,
the next becomes B, and so on. With more than 26 distinct groups (unusual for
a single section) we keep cycling A-Z; consumers should treat the string as
opaque past that point.
"""

from __future__ import annotations

from collections.abc import Iterable

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# A line's rhyme key(s): a single key (legacy callers), a set of candidate
# keys, or None/empty when nothing resolved.
LineKeys = str | Iterable[str] | None


def _as_key_set(keys: LineKeys) -> frozenset[str]:
    if keys is None:
        return frozenset()
    if isinstance(keys, str):
        return frozenset((keys,))
    return frozenset(keys)


def assign_scheme(keys: list[LineKeys]) -> tuple[str, str]:
    """Return (scheme_letters, confidence).

    Empty input returns ``("", "full")``.
    """
    if not keys:
        return "", "full"

    keysets = [_as_key_set(k) for k in keys]

    # Union-find over line indices: two lines are unioned if their key sets
    # share a key, directly or transitively.
    parent = list(range(len(keysets)))

    def find(i: int) -> int:
        while parent[i] != i:
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    first_line_for_key: dict[str, int] = {}
    for i, ks in enumerate(keysets):
        for k in ks:
            seen_at = first_line_for_key.get(k)
            if seen_at is None:
                first_line_for_key[k] = i
            else:
                union(i, seen_at)

    letter_by_root: dict[int, str] = {}
    out: list[str] = []
    confidence = "full"
    next_letter = 0
    for i, ks in enumerate(keysets):
        if not ks:
            out.append("?")
            confidence = "partial"
            continue
        root = find(i)
        letter = letter_by_root.get(root)
        if letter is None:
            letter = _ALPHABET[next_letter % len(_ALPHABET)]
            letter_by_root[root] = letter
            next_letter += 1
        out.append(letter)
    return "".join(out), confidence


__all__ = ["assign_scheme"]
