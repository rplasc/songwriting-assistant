"""Inner-rhyme detection.

End-rhyme logic (``rhyme_key`` + the draft rhyme-scheme rules) only ever looks
at the last word of each line. This module looks at *every* word and groups the
ones that rhyme with each other — interior or ending, same line or across lines
— so the UI can highlight rhyming words wherever they fall.

Highlighting is tuned for scheme clarity, not raw recall (feedback: raw
bucketing highlighted nearly every word and drowned the primary scheme):

- Function words enter groups only when they end their line.
- Every group must be *anchored* — contain a line-final or multisyllabic
  occurrence — or, for the perfect tier only, be a dense chain of
  ``_DENSE_GROUP_MIN_DISTINCT_WORDS``+ distinct words. Scattered mid-line
  monosyllable matches are pruned as noise.
- A cadence pass connects multisyllabic (3+ beat) deliveries whose rhythm
  matches even when their phonemes don't — single words anywhere in a line
  ("sandwiches"/"allowances") and compound line-ending spans ("countin'
  this"/"downin' this"). It runs before the near tier so a delivery family
  isn't split by one member being claimed into an unrelated slant group.
- An end-refrain — the same content word ending two or more lines ("…funk" /
  "…funk") — is highlighted even though it repeats: at line endings the
  repetition is the structural anchor, not noise.

Deliberately rejected: a hard top-N group cap (rank reshuffles while typing
cause highlight flicker; deterministic rules don't) and CMU stress digits for
function-word detection (CMU marks "my"/"to" stressed — the lexical list is
more reliable).

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
from app.domain.near_rhyme_rules import inner_near_rhyme_key
from app.domain.rhyme.ending_cadence_rules import (
    destress,
    ending_cadence_key,
    vowel_count,
)
from app.domain.rhyme_rules import rhyme_key
from app.models.token import Token
from app.schemas.responses import InnerRhymeGroup, RhymeOccurrence

# Returns every plausible ARPABET-style pronunciation for a token (dictionary
# pronunciations, or the top heuristic tails for unknown words), or an empty
# sequence when nothing usable was found. A word with multiple variants can
# match a rhyme group through any one of them.
PhonemesFor = Callable[[Token], "Sequence[tuple[str, ...]]"]

# Per language: (perfect-key fn, near-key fn). English uses the perfect tail
# and the strict inner slant key (NOT the suggestion path's near_rhyme_key,
# whose recall-oriented vowel classes flood lyric highlighting); Spanish uses
# consonant (perfect analog) and assonant (vowel-only) keys.
_KEY_FNS: dict[str, tuple[Callable, Callable]] = {
    "en": (rhyme_key, inner_near_rhyme_key),
    "es": (consonant_rhyme_key, assonant_rhyme_key),
}

# Per language: the key for the multisyllabic cadence pass. English only —
# Spanish's assonant key already matches vowel tails, so a looser cadence pass
# would only add noise there.
_CADENCE_KEY_FNS: dict[str, Callable] = {
    "en": ending_cadence_key,
}

# Words shorter than this are skipped — single letters ("a", "i") are phonetic
# noise that produces unhelpful highlight groups.
_MIN_WORD_LEN = 2

# Anchor pruning: a group survives only when at least one occurrence is
# line-final or has this many syllables — the "phonetic delivery weighting"
# that keeps the primary scheme visible. Perfect groups may alternatively
# survive as a dense chain of *distinct* words (cat/sat/mat mid-line is
# deliberate craft; sit/quit/quit is not — repeats padding the count let
# scattered mid-line pairs masquerade as chains). Near groups get no such
# escape hatch because scattered mid-line monosyllable slant matches are the
# dominant highlight noise.
_ANCHOR_MIN_SYLLABLES = 2
_DENSE_GROUP_MIN_DISTINCT_WORDS = 3

# Compound line-ending spans ("countin' this"): at most this many trailing
# tokens are considered when joining unstressed function words onto the
# content word that carries the line's final stress.
_MAX_SPAN_TOKENS = 3

# Unstressed-in-connected-speech function words. They enter highlight groups
# only when they end their line — a line ending on "you"/"do" is a real
# end-rhyme, but mid-line "my"/"to"/"the" matches are cognitive noise that
# drowns the scheme. They never seed near groups, and an all-function-word
# near group is suppressed — a slant match between "them" and "then" is
# noise, not craft.
_FUNCTION_WORDS: dict[str, frozenset[str]] = {
    "en": frozenset({
        "am", "an", "and", "are", "as", "at", "be", "been", "but", "by",
        "can", "could", "did", "do", "does", "for", "from", "had", "has",
        "have", "he", "her", "him", "his", "how", "if", "in", "is", "it",
        "its", "may", "me", "might", "must", "my", "no", "nor", "not", "of",
        "off", "on", "or", "our", "shall", "she", "should", "so", "than",
        "that", "the", "their", "them", "then", "these", "they", "this",
        "those", "to", "too", "us", "was", "we", "were", "what", "when",
        "who", "why", "will", "with", "would", "you", "your",
        "ain't", "can't", "don't", "didn't", "isn't", "it's", "i'd", "i'll",
        "i'm", "i've", "that's", "they're", "wasn't", "we're", "won't",
        "you're",
    }),
    "es": frozenset({
        "al", "como", "con", "de", "del", "el", "en", "es", "esa", "ese",
        "esta", "este", "la", "las", "le", "les", "lo", "los", "me", "mi",
        "mis", "nos", "para", "pero", "por", "que", "se", "si", "son", "su",
        "sus", "te", "tu", "tus", "un", "una", "unas", "unos", "ya",
    }),
}


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


# Per-occurrence metadata recorded during the token walk, keyed by
# (line_index, word_index): (is_line_final, max syllables across variants).
_OccMeta = dict[tuple[int, int], tuple[bool, int]]


def _is_anchored(
    occ: Sequence[RhymeOccurrence],
    meta: _OccMeta,
    *,
    allow_dense: bool,
) -> bool:
    """Anchor pruning: the group must contain a line-final or multisyllabic
    occurrence, or (perfect tier only) be a dense chain of distinct words."""
    for o in occ:
        is_line_final, syllables = meta.get((o.line_index, o.word_index), (False, 0))
        if is_line_final or syllables >= _ANCHOR_MIN_SYLLABLES:
            return True
    return (
        allow_dense
        and len({o.normalized for o in occ}) >= _DENSE_GROUP_MIN_DISTINCT_WORDS
    )


def _build_groups(
    buckets: dict[str, list[RhymeOccurrence]],
    *,
    language: str,
    rhyme_type: str,
    confidence: str,
    function_words: frozenset[str],
    meta: _OccMeta,
) -> list[InnerRhymeGroup]:
    groups: list[InnerRhymeGroup] = []
    for key, occ in buckets.items():
        if len(occ) < 2:
            continue
        # Need at least two *distinct* words so plain repetition (handled by
        # repetition_rules) isn't mislabeled rhyme — EXCEPT when the same
        # content word ends two or more lines: an end-refrain ("…funk" /
        # "…funk") is the structural anchor of its bars and belongs in the
        # highlight even though it repeats.
        if len({o.normalized for o in occ}) < 2 and not (
            rhyme_type == "perfect"
            and occ[0].normalized not in function_words
            and len({o.line_index for o in occ}) >= 2
            and all(
                meta.get((o.line_index, o.word_index), (False, 0))[0] for o in occ
            )
        ):
            continue
        # Function words reach the perfect tier only when line-final, so
        # an all-function-word perfect group is a legitimate end-rhyme. A
        # near/slant match between function words ("them"/"then") is noise, so
        # all-function-word groups are still suppressed in the near tier.
        if rhyme_type == "near" and all(o.normalized in function_words for o in occ):
            continue
        if not _is_anchored(occ, meta, allow_dense=rhyme_type == "perfect"):
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


def _ending_span(
    entries: Sequence[tuple[Token, Sequence[tuple[str, ...]], RhymeOccurrence]],
    function_words: frozenset[str],
) -> tuple[tuple[str, ...], list[RhymeOccurrence]] | None:
    """Compound line-ending span: trailing function words + their stress anchor.

    Walks back from the line's final token collecting function words, then
    stops at the first content token — the word that carries the ending's
    stress ("countin'" in "countin' this"). Returns the concatenated phonemes
    (first pronunciation variant of each token; function-word tails
    destressed) and the occurrences to highlight as one unit, or ``None``
    when the line ends directly on a content word (single-word candidacy
    already covers it), the trailing function run is longer than
    ``_MAX_SPAN_TOKENS - 1``, or no content anchor exists.
    """
    tail: list[tuple[Token, Sequence[tuple[str, ...]], RhymeOccurrence]] = []
    anchor: tuple[Token, Sequence[tuple[str, ...]], RhymeOccurrence] | None = None
    for entry in reversed(entries[-_MAX_SPAN_TOKENS:]):
        if entry[0].normalized in function_words:
            tail.append(entry)
        else:
            anchor = entry
            break
    if anchor is None or not tail:
        return None
    span = [anchor, *reversed(tail)]
    phonemes: list[str] = []
    occs: list[RhymeOccurrence] = []
    for i, (_, variants, occ) in enumerate(span):
        phonemes.extend(variants[0] if i == 0 else destress(variants[0]))
        occs.append(occ)
    return tuple(phonemes), occs


def find_inner_rhyme_groups(
    lines: Sequence[tuple[int, Sequence[Token]]],
    phonemes_for: PhonemesFor,
    language: str,
) -> list[InnerRhymeGroup]:
    """Group rhyming words across ``lines`` into highlight groups.

    ``lines`` is a sequence of ``(line_index, tokens)``; ``line_index`` is echoed
    onto each occurrence (1-based global for drafts, 0 for the single-line
    endpoint). Perfect rhymes take precedence; multisyllabic cadences (single
    words anywhere, plus compound line-ending spans like "countin' this") come
    next; remaining words are matched on the coarser near/slant key. Groups
    that fail anchor pruning are dropped.
    """
    perfect_fn, near_fn = _KEY_FNS.get(language, (rhyme_key, inner_near_rhyme_key))
    cadence_fn = _CADENCE_KEY_FNS.get(language)
    function_words = _FUNCTION_WORDS.get(language, frozenset())

    perfect_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    # Near/cadence candidates keep their occurrences + key set so we can
    # bucket the ones that survive the earlier tiers.
    near_candidates: list[tuple[set[str], RhymeOccurrence]] = []
    cadence_candidates: list[tuple[set[str], list[RhymeOccurrence]]] = []
    meta: _OccMeta = {}

    for line_index, tokens in lines:
        entries: list[tuple[Token, Sequence[tuple[str, ...]], RhymeOccurrence]] = []
        for token in tokens:
            if len(token.normalized) < _MIN_WORD_LEN:
                continue
            variants = phonemes_for(token)
            if not variants:
                continue
            entries.append((token, variants, _occurrence(line_index, token)))
        for pos, (token, variants, occ) in enumerate(entries):
            is_line_final = pos == len(entries) - 1
            meta[(occ.line_index, occ.word_index)] = (
                is_line_final,
                max(vowel_count(v) for v in variants),
            )
            is_function = token.normalized in function_words
            # Function words highlight only at line end — mid-line
            # "my"/"to"/"the" matches drown the scheme.
            if not is_function or is_line_final:
                perfect_keys = {k for v in variants if (k := perfect_fn(v)) is not None}
                for key in perfect_keys:
                    perfect_buckets_raw.setdefault(key, []).append(occ)
            # Function words only count when the sound match is exact — they
            # never seed slant or cadence groups (though they may ride along
            # in a compound span, below).
            if is_function:
                continue
            near_keys = {k for v in variants if (k := near_fn(v)) is not None}
            if near_keys:
                near_candidates.append((near_keys, occ))
            # Cadence candidacy is position-independent: the key itself
            # requires a 3+ syllable tail, so only long multisyllabic
            # deliveries ("sandwiches" mid-line) qualify.
            if cadence_fn is not None:
                cadence_keys = {k for v in variants if (k := cadence_fn(v)) is not None}
                if cadence_keys:
                    cadence_candidates.append((cadence_keys, [occ]))
        # Compound line-ending span: trailing function words joined onto the
        # content word carrying the line's final stress, so "countin' this" /
        # "downin' this" rhyme as units. Function-word phonemes are destressed
        # (dictionary stress on "this" would hijack the anchor).
        if cadence_fn is not None and len(entries) >= 2:
            span = _ending_span(entries, function_words)
            if span is not None:
                span_phonemes, span_occs = span
                key = cadence_fn(span_phonemes)
                if key is not None:
                    cadence_candidates.append(({key}, span_occs))

    perfect_buckets = _merge_multi_key_buckets(perfect_buckets_raw)
    perfect_groups = _build_groups(
        perfect_buckets,
        language=language,
        rhyme_type="perfect",
        confidence="high",
        function_words=function_words,
        meta=meta,
    )

    # Positions already claimed by a perfect group are excluded from the
    # looser tiers; the cadence pass runs before near so a delivery family
    # ("sandwiches"/"allowances"/"countin' this") isn't split by one member
    # being claimed into an unrelated slant group first.
    claimed: set[tuple[int, int]] = {
        (o.line_index, o.word_index)
        for group in perfect_groups
        for o in group.occurrences
    }
    cadence_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    for cadence_keys, occs in cadence_candidates:
        if any((o.line_index, o.word_index) in claimed for o in occs):
            continue
        for key in cadence_keys:
            cadence_buckets_raw.setdefault(key, []).extend(occs)

    cadence_buckets = _merge_multi_key_buckets(cadence_buckets_raw)
    # Emitted as near/medium — no schema ripple, and the client de-emphasizes
    # them the same way.
    cadence_groups = _build_groups(
        cadence_buckets,
        language=language,
        rhyme_type="near",
        confidence="medium",
        function_words=function_words,
        meta=meta,
    )

    claimed.update(
        (o.line_index, o.word_index)
        for group in cadence_groups
        for o in group.occurrences
    )
    near_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    for near_keys, occ in near_candidates:
        if (occ.line_index, occ.word_index) in claimed:
            continue
        for key in near_keys:
            near_buckets_raw.setdefault(key, []).append(occ)

    near_buckets = _merge_multi_key_buckets(near_buckets_raw)
    near_groups = _build_groups(
        near_buckets,
        language=language,
        rhyme_type="near",
        confidence="medium",
        function_words=function_words,
        meta=meta,
    )

    groups = perfect_groups + cadence_groups + near_groups
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
