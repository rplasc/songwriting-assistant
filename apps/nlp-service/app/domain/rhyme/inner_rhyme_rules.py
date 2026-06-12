"""Inner-rhyme detection.

End-rhyme logic (``rhyme_key`` + the draft rhyme-scheme rules) only ever looks
at the last word of each line. This module looks at *every* word and groups the
ones that rhyme with each other — interior or ending, same line or across lines
— so the UI can highlight rhyming words wherever they fall.

The detector is fed positioned tokens plus a ``phonemes_for`` callable, keeping
it decoupled from ``LanguageContext``. Two convenience builders construct that
callable for English and Spanish, caching by normalized word per request.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

from app.domain.heuristic_g2p import (
    MAX_HEURISTIC_TAIL_VARIANTS,
    heuristic_phoneme_tails,
)
from app.domain.languages.spanish.g2p import g2p as spanish_g2p
from app.domain.languages.spanish.rhyme_rules import (
    assonant_rhyme_key,
    consonant_rhyme_key,
)
from app.domain.near_rhyme_rules import near_rhyme_key
from app.domain.rhyme_rules import rhyme_key
from app.models.token import Token
from app.schemas.responses import InnerRhymeGroup, RhymeOccurrence

# Returns every plausible ARPABET-style pronunciation for a token (dictionary
# pronunciations, or the top heuristic tails for unknown words), or an empty
# sequence when nothing usable was found. A word with multiple variants can
# match a rhyme group through any one of them.
PhonemesFor = Callable[[Token], "Sequence[tuple[str, ...]]"]

# Per language: (perfect-key fn, near-key fn). English uses the perfect tail and
# the manner-of-articulation slant key; Spanish uses consonant (perfect analog)
# and assonant (vowel-only) keys.
_KEY_FNS: dict[str, tuple[Callable, Callable]] = {
    "en": (rhyme_key, near_rhyme_key),
    "es": (consonant_rhyme_key, assonant_rhyme_key),
}

# Words shorter than this are skipped — single letters ("a", "i") are phonetic
# noise that produces unhelpful highlight groups.
_MIN_WORD_LEN = 2


def english_phonemes_for(pronunciation_service, cache: dict[str, list[tuple[str, ...]]]) -> PhonemesFor:
    """Build a token -> phoneme-variants lookup for English, dictionary first
    then heuristic. Mirrors ``_english_rhyme_key`` in the draft service.

    Returns every dictionary pronunciation for the word (heteronyms like
    "read" carry more than one), or — when the dictionary has none — the top
    ``MAX_HEURISTIC_TAIL_VARIANTS`` heuristic tails.
    """

    def _lookup(token: Token) -> list[tuple[str, ...]]:
        norm = token.normalized
        if norm in cache:
            return cache[norm]
        variants: list[tuple[str, ...]] = []
        seen: set[tuple[str, ...]] = set()
        _, prons = pronunciation_service.lookup(token.text)
        for pron in prons:
            if pron.phonemes:
                phonemes = tuple(pron.phonemes)
                if phonemes not in seen:
                    seen.add(phonemes)
                    variants.append(phonemes)
        if not variants and norm:
            tails = heuristic_phoneme_tails(norm)
            variants = [tuple(t) for t in tails[:MAX_HEURISTIC_TAIL_VARIANTS]]
        cache[norm] = variants
        return variants

    return _lookup


def spanish_phonemes_for(cache: dict[str, list[tuple[str, ...]]]) -> PhonemesFor:
    """Build a token -> phoneme-variants lookup for Spanish via rule-based G2P."""

    def _lookup(token: Token) -> list[tuple[str, ...]]:
        norm = token.normalized
        if norm in cache:
            return cache[norm]
        variants: list[tuple[str, ...]] = []
        if norm:
            pron = spanish_g2p(norm)
            if pron.phonemes:
                variants.append(tuple(pron.phonemes))
        cache[norm] = variants
        return variants

    return _lookup


def phonemes_for_context(ctx, cache: dict[str, list[tuple[str, ...]]]) -> PhonemesFor:
    """Pick the right phoneme lookup for a LanguageContext's engine.

    Kept duck-typed (``ctx.engine.code`` + ``ctx.pronunciation_service``) so the
    domain layer doesn't import ``LanguageContext``. Falls back to the English
    lookup for any unrecognized engine code.
    """
    if getattr(ctx.engine, "code", "en") == "es":
        return spanish_phonemes_for(cache)
    return english_phonemes_for(ctx.pronunciation_service, cache)


def _occurrence(line_index: int, token: Token) -> RhymeOccurrence:
    return RhymeOccurrence(
        line_index=line_index,
        word_index=token.index if token.index is not None else 0,
        char_start=token.char_start if token.char_start is not None else 0,
        char_end=token.char_end if token.char_end is not None else 0,
        text=token.text,
        normalized=token.normalized,
    )


def _group_id(language: str, rhyme_type: str, key: str, occ: Sequence[RhymeOccurrence]) -> str:
    positions = ",".join(f"{o.line_index}:{o.word_index}" for o in occ)
    raw = f"{language}|{rhyme_type}|{key}|{positions}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"irh_{digest}"


def _merge_multi_key_buckets(
    buckets: dict[str, list[RhymeOccurrence]],
) -> dict[str, list[RhymeOccurrence]]:
    """Merge key buckets that share an occurrence into one.

    A word with multiple pronunciations or heuristic tails can land in more
    than one key bucket (e.g. the heteronym "read" matches both an IY-tail
    key and an EH-tail key). Buckets that share at least one occurrence
    describe the same rhyme family from that word's point of view, so they're
    unioned together — letting a word join any bucket where some variant
    matches, with the merge transitively pulling in the other words on each
    side too.
    """
    if not buckets:
        return {}

    parent: dict[str, str] = {key: key for key in buckets}

    def find(key: str) -> str:
        while parent[key] != key:
            key = parent[key]
        return key

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    occ_to_keys: dict[tuple[int, int], list[str]] = {}
    for key, occs in buckets.items():
        for occ in occs:
            occ_to_keys.setdefault((occ.line_index, occ.word_index), []).append(key)
    for keys in occ_to_keys.values():
        for k in keys[1:]:
            union(keys[0], k)

    merged: dict[str, list[RhymeOccurrence]] = {}
    seen: dict[str, set[tuple[int, int]]] = {}
    for key, occs in buckets.items():
        canonical = min(k for k in buckets if find(k) == find(key))
        bucket = merged.setdefault(canonical, [])
        seen_set = seen.setdefault(canonical, set())
        for occ in occs:
            pos = (occ.line_index, occ.word_index)
            if pos not in seen_set:
                seen_set.add(pos)
                bucket.append(occ)
    return merged


def _build_groups(
    buckets: dict[str, list[RhymeOccurrence]],
    *,
    language: str,
    rhyme_type: str,
    confidence: str,
) -> list[InnerRhymeGroup]:
    groups: list[InnerRhymeGroup] = []
    for key, occ in buckets.items():
        # Need at least two rhyming words, and at least two *distinct* words so
        # plain repetition (handled by repetition_rules) isn't mislabeled rhyme.
        if len(occ) < 2 or len({o.normalized for o in occ}) < 2:
            continue
        ordered = sorted(occ, key=lambda o: (o.line_index, o.word_index))
        groups.append(
            InnerRhymeGroup(
                id=_group_id(language, rhyme_type, key, ordered),
                rhyme_type=rhyme_type,
                confidence=confidence,
                rhyme_key=key,
                occurrences=ordered,
            )
        )
    return groups


def find_inner_rhyme_groups(
    lines: Sequence[tuple[int, Sequence[Token]]],
    phonemes_for: PhonemesFor,
    language: str,
) -> list[InnerRhymeGroup]:
    """Group rhyming words across ``lines`` into highlight groups.

    ``lines`` is a sequence of ``(line_index, tokens)``; ``line_index`` is echoed
    onto each occurrence (1-based global for drafts, 0 for the single-line
    endpoint). Perfect rhymes take precedence; remaining words are matched on the
    coarser near/slant key.
    """
    perfect_fn, near_fn = _KEY_FNS.get(language, (rhyme_key, near_rhyme_key))

    perfect_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    # Each near candidate keeps its occurrence + near-key set so we can bucket
    # the ones that survive perfect-grouping.
    near_candidates: list[tuple[set[str], RhymeOccurrence]] = []

    for line_index, tokens in lines:
        for token in tokens:
            if len(token.normalized) < _MIN_WORD_LEN:
                continue
            variants = phonemes_for(token)
            if not variants:
                continue
            occ = _occurrence(line_index, token)
            perfect_keys = {k for v in variants if (k := perfect_fn(v)) is not None}
            for key in perfect_keys:
                perfect_buckets_raw.setdefault(key, []).append(occ)
            near_keys = {k for v in variants if (k := near_fn(v)) is not None}
            if near_keys:
                near_candidates.append((near_keys, occ))

    perfect_buckets = _merge_multi_key_buckets(perfect_buckets_raw)
    perfect_groups = _build_groups(
        perfect_buckets, language=language, rhyme_type="perfect", confidence="high"
    )

    # Positions already claimed by a perfect group are excluded from near groups.
    claimed: set[tuple[int, int]] = {
        (o.line_index, o.word_index)
        for group in perfect_groups
        for o in group.occurrences
    }
    near_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    for near_keys, occ in near_candidates:
        if (occ.line_index, occ.word_index) in claimed:
            continue
        for key in near_keys:
            near_buckets_raw.setdefault(key, []).append(occ)

    near_buckets = _merge_multi_key_buckets(near_buckets_raw)
    near_groups = _build_groups(
        near_buckets, language=language, rhyme_type="near", confidence="medium"
    )

    groups = perfect_groups + near_groups
    # Stable ordering: by first occurrence, perfect before near on ties.
    groups.sort(
        key=lambda g: (
            g.occurrences[0].line_index,
            g.occurrences[0].word_index,
            0 if g.rhyme_type == "perfect" else 1,
        )
    )
    return groups


__all__ = [
    "find_inner_rhyme_groups",
    "english_phonemes_for",
    "spanish_phonemes_for",
    "PhonemesFor",
]
