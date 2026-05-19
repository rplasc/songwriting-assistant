"""Spanish syllabification.

Rule-based splitter. Inputs are normalized Spanish words (lowercase, with
ñ and accented vowels preserved). The algorithm:

  1. Tokenize letters, treating ``ch``/``ll``/``rr`` as atomic consonants,
     and ``qu`` / ``gu``-before-front-vowel (silent ``u``) likewise. This
     keeps "guerra" → ``gue-rra`` rather than ``gue-r-ra``.
  2. Group adjacent vowels into nuclei using diphthong/hiatus rules.
     Diphthong = strong+weak / weak+strong / weak+weak with no accent on
     a weak vowel. Triphthong = weak+strong+weak with no accent on the
     weak vowels. Anything else is hiatus.
  3. Split intervocalic consonant clusters: single consonant joins the
     following nucleus; two consonants split unless the pair is a valid
     onset (``pl pr bl br cl cr dr fl fr gl gr tr tl``); larger clusters
     keep the trailing ``Cr/Cl`` onset with the next syllable.

Returns ``(syllables, stress_index)`` so callers can locate the stressed
syllable without re-deriving the rules. Stress logic lives in
:mod:`app.domain.languages.spanish.stress`.
"""

from __future__ import annotations

from app.domain.languages.spanish.stress import stressed_syllable_index

_STRONG_VOWELS: frozenset[str] = frozenset("aeoáéó")
# Weak vowels with no accent — these are the ones that form diphthongs.
_WEAK_UNACCENTED: frozenset[str] = frozenset("iuü")
# Weak vowels WITH a written accent — these force hiatus.
_WEAK_ACCENTED: frozenset[str] = frozenset("íú")
_VOWELS: frozenset[str] = _STRONG_VOWELS | _WEAK_UNACCENTED | _WEAK_ACCENTED

# Two-letter onsets that stay attached as a single onset cluster.
# ``tl`` is included for Latin-American defaults (Nahuatl-derived loans).
_VALID_ONSETS: frozenset[str] = frozenset(
    {"pl", "pr", "bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "tr", "tl"}
)

# Inseparable digraphs at the consonant level (treated as one phonetic unit).
_INSEPARABLE_DIGRAPHS: frozenset[str] = frozenset({"ch", "ll", "rr"})


def _is_vowel(ch: str) -> bool:
    return ch in _VOWELS


def _is_strong(ch: str) -> bool:
    return ch in _STRONG_VOWELS


def _is_weak_unaccented(ch: str) -> bool:
    return ch in _WEAK_UNACCENTED


def _forms_diphthong(a: str, b: str) -> bool:
    # Two adjacent vowels stay in one nucleus unless both are strong, or one
    # of them is a weak vowel that bears a written accent (which pins stress
    # and forces the run apart).
    if a in _WEAK_ACCENTED or b in _WEAK_ACCENTED:
        return False
    if _is_strong(a) and _is_strong(b):
        return False
    return True


def _is_triphthong(a: str, b: str, c: str) -> bool:
    return (
        _is_weak_unaccented(a)
        and _is_strong(b)
        and _is_weak_unaccented(c)
    )


def _tokenize_letters(word: str) -> list[tuple[str, bool]]:
    """Walk left-to-right, emitting (text, is_vowel) tokens. Digraphs become
    a single token so consonant-cluster math works on phonetic units."""
    out: list[tuple[str, bool]] = []
    i = 0
    n = len(word)
    while i < n:
        if i + 1 < n:
            pair = word[i : i + 2]
            if pair in _INSEPARABLE_DIGRAPHS:
                out.append((pair, False))
                i += 2
                continue
            if pair == "qu":
                # Spanish ``qu`` only appears before ``e``/``i`` and the u is
                # silent. Treat the digraph as one consonant for splitting.
                out.append((pair, False))
                i += 2
                continue
            if pair == "gu" and i + 2 < n and word[i + 2] in "eiéí":
                # Silent-u ``gu``: ``guerra``, ``guitarra``. ``gua``/``guo``
                # / ``güe`` / ``güi`` are NOT this case — those leave the u
                # (or ü) as a real vowel, so we drop through.
                out.append((pair, False))
                i += 2
                continue
        ch = word[i]
        out.append((ch, _is_vowel(ch)))
        i += 1
    return out


def _split_vowel_run(run: list[str]) -> list[list[str]]:
    """Partition a consecutive vowel sequence into syllable nuclei."""
    if not run:
        return []
    if len(run) >= 3 and _is_triphthong(run[0], run[1], run[2]):
        rest = _split_vowel_run(run[3:])
        return [run[:3]] + rest
    if len(run) >= 2 and _forms_diphthong(run[0], run[1]):
        rest = _split_vowel_run(run[2:])
        return [run[:2]] + rest
    return [[run[0]]] + _split_vowel_run(run[1:])


def _split_consonant_cluster(cluster_size: int, cluster_tokens: list[str]) -> int:
    """Return how many of the leading consonants stay with the LEFT syllable.

    Cluster tokens are the phonetic-letter strings (so ``ll`` is one token).
    """
    if cluster_size <= 1:
        return 0
    if cluster_size == 2:
        pair = cluster_tokens[0] + cluster_tokens[1]
        if pair in _VALID_ONSETS:
            return 0
        return 1
    if cluster_size == 3:
        # Try keeping the trailing two as the onset of the next syllable.
        pair = cluster_tokens[1] + cluster_tokens[2]
        if pair in _VALID_ONSETS:
            return 1
        return 2
    # 4+ consonants: keep the trailing two with the right syllable if they
    # form a valid onset; otherwise split right down the middle of the cluster.
    pair = cluster_tokens[-2] + cluster_tokens[-1]
    if pair in _VALID_ONSETS:
        return cluster_size - 2
    return cluster_size - 1


def syllabify(word: str) -> tuple[list[str], int]:
    """Return ``(syllables, stress_index)`` for a normalized Spanish word.

    ``stress_index`` is the index into ``syllables`` of the stressed
    syllable. For empty input the function returns ``([word], 0)`` so
    callers always have a valid pair.
    """
    if not word:
        return [word], 0

    tokens = _tokenize_letters(word)
    n = len(tokens)

    # Find nuclei as ordered groups of token indices.
    nuclei: list[list[int]] = []
    i = 0
    while i < n:
        if tokens[i][1]:
            j = i
            while j + 1 < n and tokens[j + 1][1]:
                j += 1
            run_chars = [tokens[k][0] for k in range(i, j + 1)]
            sub_nuclei = _split_vowel_run(run_chars)
            cursor = i
            for nuc in sub_nuclei:
                count = len(nuc)
                nuclei.append(list(range(cursor, cursor + count)))
                cursor += count
            i = j + 1
        else:
            i += 1

    if not nuclei:
        return [word], 0

    # Build syllable spans (start_idx, end_idx_inclusive into tokens).
    spans: list[tuple[int, int]] = []
    syllable_start = 0
    for idx, nuc in enumerate(nuclei):
        if idx + 1 < len(nuclei):
            next_nuc = nuclei[idx + 1]
            cons_indices = list(range(nuc[-1] + 1, next_nuc[0]))
            cons_tokens = [tokens[k][0] for k in cons_indices]
            keep_left = _split_consonant_cluster(len(cons_indices), cons_tokens)
            if keep_left == 0:
                end = nuc[-1]
                next_start = cons_indices[0] if cons_indices else next_nuc[0]
            else:
                end = cons_indices[keep_left - 1]
                next_start = (
                    cons_indices[keep_left]
                    if keep_left < len(cons_indices)
                    else next_nuc[0]
                )
            spans.append((syllable_start, end))
            syllable_start = next_start
        else:
            # Last syllable absorbs all remaining trailing tokens.
            spans.append((syllable_start, n - 1))

    syllables = [
        "".join(tokens[k][0] for k in range(s, e + 1)) for s, e in spans
    ]
    return syllables, stressed_syllable_index(syllables, word)
