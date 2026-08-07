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
- A group must span two distinct *line texts*. A repeated chorus otherwise
  makes every one of its words rhyme with its own echo, painting the whole
  refrain in as many colors as it has words.
- A cadence pass connects multisyllabic (3+ beat) deliveries whose rhythm
  matches even when their phonemes don't — single words anywhere in a line
  ("sandwiches"/"allowances") and compound line-ending spans ("countin'
  this"/"downin' this"). It runs before the near tier so a delivery family
  isn't split by one member being claimed into an unrelated slant group.
- An end-refrain — the same content word ending two or more lines ("…funk" /
  "…funk") — is highlighted even though it repeats: at line endings the
  repetition is the structural anchor, not noise.
- Identical trailing function words join their anchors' group ("countin'
  *this*" / "downin' *this*"), so compound phrases highlight as units.
- OOV lyric vocabulary is recovered before guessing: dropped-g forms look up
  their "-ing" spelling, compounds split into dictionary halves, and the
  remaining guesses never claim perfect rhymes (``HeuristicTailVariants``).

Spanish needs a stricter hand than English, because its phonology makes the
English thresholds vacuous:

- Assonance (the near tier for Spanish) is scoped to **line endings only**.
  With five vowels, any two two-syllable words share an assonant key about one
  time in twenty-five, so mid-line assonance is closer to coincidence than
  craft — and *rima asonante* is defined on line endings in Spanish verse
  anyway.
- The multisyllabic anchor threshold is higher (``_ANCHOR_MIN_SYLLABLES``):
  almost every Spanish word clears two syllables, so at two the anchor rule
  prunes nothing at all.
- Syllables are counted by the engine's syllabifier rather than by counting
  vowel phonemes, because Spanish G2P emits one vowel per vowel *letter* —
  the diphthongs in "bien" and "dios" would otherwise read as two syllables.

Deliberately rejected: a hard top-N group cap (rank reshuffles while typing
cause highlight flicker; deterministic rules don't) and CMU stress digits for
function-word detection (CMU marks "my"/"to" stressed — the lexical list is
more reliable).

The detector is fed positioned tokens plus a ``phonemes_for`` callable (and
optionally a ``syllables_for`` one), keeping it decoupled from
``LanguageContext``. Convenience builders construct those callables for English
and Spanish, caching by normalized word per request.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

from app.domain.heuristic_g2p import (
    MAX_HEURISTIC_TAIL_VARIANTS,
    heuristic_full_reading,
    heuristic_phoneme_tails,
)
from app.domain.languages.spanish.function_words import SPANISH_FUNCTION_WORDS
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

# Returns a token's syllable count, for languages where counting vowel
# phonemes is wrong (see ``spanish_syllables_for``). Optional — omitting it
# falls back to the vowel count across the token's phoneme variants.
SyllablesFor = Callable[[Token], int]

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
#
# The syllable bar is per language. English monosyllables are common enough
# that two syllables already marks a word as deliberate; Spanish words are
# overwhelmingly two syllables or more, so at two the test admits everything
# and prunes nothing. Three is where a Spanish mid-line match stops looking
# like an accident of a five-vowel inventory.
_ANCHOR_MIN_SYLLABLES: dict[str, int] = {"en": 2, "es": 3}
_ANCHOR_MIN_SYLLABLES_DEFAULT = 2
_DENSE_GROUP_MIN_DISTINCT_WORDS = 3

# Languages whose near tier is restricted to line-final words. Spanish
# assonance matches vowels only, and with five vowels two arbitrary two-syllable
# words share a key roughly one time in twenty-five — mid-line, that is noise
# rather than craft. Scoping it to line endings also matches how *rima asonante*
# is defined in Spanish verse, where the ending is what carries the rhyme.
_NEAR_TIER_LINE_FINAL_ONLY = frozenset({"es"})

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
    # The canonical list the rest of the Spanish engine uses, plus the two
    # copulas. A hand-rolled copy used to live here and had drifted badly: it
    # was missing "no", "hasta", "más", "tú", "sin", "ni" and every other
    # accented entry, so those highlighted as content words.
    "es": SPANISH_FUNCTION_WORDS | {"es", "son"},
}


class HeuristicTailVariants(list):
    """Marker for variants that are heuristic *tails*, not full pronunciations.

    Tail guesses cover one syllable of fabricated stress readings ("tetris" →
    IH0/IH1/IH2 + S), which is fine for slant matching but poison for the
    perfect tier: a fabricated ``IH1 S`` tail is indistinguishable from a real
    exact match and pairs unknown words with function words like "this". The
    detector skips perfect bucketing for these variants; near/cadence tiers
    still see them.
    """


def _demote_primary_stress(phonemes: tuple[str, ...]) -> tuple[str, ...]:
    """Primary stress → secondary, matching how CMU marks compound second
    halves ("paystub" → P EY1 S T AH2 B, not two primaries)."""
    return tuple(
        p[:-1] + "2" if p and p[-1] == "1" else p for p in phonemes
    )


def _has_stressed_vowel(phonemes: tuple[str, ...]) -> bool:
    return any(p and p[-1] in ("1", "2") for p in phonemes)


def _dictionary_variants(pronunciation_service, word: str) -> list[tuple[str, ...]]:
    variants: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    _, prons = pronunciation_service.lookup(word)
    for pron in prons:
        if pron.phonemes:
            phonemes = tuple(pron.phonemes)
            if phonemes not in seen:
                seen.add(phonemes)
                variants.append(phonemes)
    return variants


def _compound_split_variants(
    pronunciation_service, norm: str
) -> list[tuple[str, ...]]:
    """OOV compounds split into two dictionary words ("paystub" → pay + stub).

    Longest left part wins; both parts need ≥ 3 letters and the left part must
    carry a stressed vowel. The right half's primary stress is demoted to
    secondary so the rhyme keys anchor on the left half, as CMU does for real
    compounds.
    """
    if len(norm) < 6:
        return []
    for i in range(len(norm) - 3, 2, -1):
        left = _dictionary_variants(pronunciation_service, norm[:i])
        if not left or not _has_stressed_vowel(left[0]):
            continue
        right = _dictionary_variants(pronunciation_service, norm[i:])
        if not right:
            continue
        return [left[0] + _demote_primary_stress(right[0])]
    return []


def english_phonemes_for(pronunciation_service, cache: dict[str, list[tuple[str, ...]]]) -> PhonemesFor:
    """Build a token -> phoneme-variants lookup for English, dictionary first
    then heuristic. Mirrors ``_english_rhyme_key`` in the draft service.

    Returns every dictionary pronunciation for the word (heteronyms like
    "read" carry more than one). For words the dictionary misses, three
    fallbacks run in order:

    1. **Dropped-g recovery** — "countin'" normalizes to "countin"; looking up
       "counting" recovers the full pronunciation, which is what lets "-in'"
       words join real rhyme groups and compound spans.
    2. **Compound split** — "paystub" → "pay" + "stub", concatenated with the
       right half's stress demoted (see ``_compound_split_variants``).
    3. **Heuristic tails**, wrapped in ``HeuristicTailVariants`` so the
       detector keeps them out of the perfect tier.
    """

    def _lookup(token: Token) -> list[tuple[str, ...]]:
        norm = token.normalized
        if norm in cache:
            return cache[norm]
        variants: list[tuple[str, ...]] = _dictionary_variants(
            pronunciation_service, token.text
        )
        if not variants and norm:
            if norm.endswith("in"):
                variants = _dictionary_variants(pronunciation_service, norm + "g")
            if not variants:
                variants = _compound_split_variants(pronunciation_service, norm)
            if not variants:
                guesses: list[tuple[str, ...]] = []
                # Full reading first: spans and syllable metadata use
                # variants[0], and the full reading is the only guess with
                # more than the final syllable.
                full = heuristic_full_reading(norm)
                if full is not None:
                    guesses.append(full)
                guesses.extend(
                    tuple(t)
                    for t in heuristic_phoneme_tails(norm)[
                        :MAX_HEURISTIC_TAIL_VARIANTS
                    ]
                )
                variants = HeuristicTailVariants(guesses)
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


def spanish_syllables_for(cache: dict[str, int]) -> SyllablesFor:
    """Build a token -> syllable-count lookup for Spanish.

    Spanish G2P emits one vowel phoneme per vowel *letter*, so counting vowels
    in the phoneme string turns the diphthongs in "bien" and "dios" into two
    syllables apiece and lets true monosyllables clear the multisyllabic anchor
    bar. The rule-based syllabifier behind ``spanish_g2p`` is exact, so use it.
    """

    def _count(token: Token) -> int:
        norm = token.normalized
        if norm not in cache:
            cache[norm] = max(spanish_g2p(norm).syllables, 1) if norm else 1
        return cache[norm]

    return _count


def syllables_for_context(ctx) -> SyllablesFor | None:
    """Pick the syllable counter for a LanguageContext's engine, or ``None``.

    ``None`` means "count vowel phonemes", which is right for English: CMU
    marks one vowel per syllable, so the phonemes already carry the count.
    """
    if getattr(ctx.engine, "code", "en") == "es":
        return spanish_syllables_for({})
    return None


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
    min_syllables: int,
) -> bool:
    """Anchor pruning: the group must contain a line-final or multisyllabic
    occurrence, or (perfect tier only) be a *same-line* dense chain of
    distinct words. The same-line requirement is what "dense" means — a
    cat/sat/mat run inside one bar is deliberate craft, while the same three
    sounds scattered across distant lines (sit … get/let … quit) are
    coincidence, exactly the mid-line monosyllable noise the anchor rule
    exists to prune."""
    for o in occ:
        is_line_final, syllables = meta.get((o.line_index, o.word_index), (False, 0))
        if is_line_final or syllables >= min_syllables:
            return True
    return (
        allow_dense
        and len({o.normalized for o in occ}) >= _DENSE_GROUP_MIN_DISTINCT_WORDS
        and len({o.line_index for o in occ}) == 1
    )


def _build_groups(
    buckets: dict[str, list[RhymeOccurrence]],
    *,
    language: str,
    rhyme_type: str,
    confidence: str,
    function_words: frozenset[str],
    meta: _OccMeta,
    line_signatures: dict[int, str],
    min_syllables: int,
) -> list[InnerRhymeGroup]:
    groups: list[InnerRhymeGroup] = []
    for key, occ in buckets.items():
        if len(occ) < 2:
            continue
        # A group has to say something two distinct *lines* agree on. Keying
        # the footprint on the line's text rather than its number collapses a
        # repeated chorus onto itself: without this, every word of a repeated
        # refrain rhymes with its own echo, and a four-word hook paints four
        # colors that mean nothing. Surviving groups keep all their
        # occurrences, so a repeat still highlights the same way it first did.
        if len({(line_signatures.get(o.line_index, ""), o.word_index) for o in occ}) < 2:
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
        if not _is_anchored(
            occ,
            meta,
            allow_dense=rhyme_type == "perfect",
            min_syllables=min_syllables,
        ):
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


def _extend_function_tails(
    groups: list[InnerRhymeGroup],
    line_entries: dict[int, list[tuple[bool, RhymeOccurrence]]],
    *,
    language: str,
    taken: set[tuple[int, int]],
) -> list[InnerRhymeGroup]:
    """Pull identical trailing function words into their anchors' group.

    When two or more members of a group are each followed by the same run of
    function words to the end of their lines — "countin' *this*" / "downin'
    *this*" — the phrases rhyme as compound units, and the writer reads them
    as such. The tail words join the group (and are marked ``taken`` so later
    tiers leave them alone), letting the editor paint each phrase as one
    continuous block. Groups without a repeated tail signature pass through
    untouched.
    """
    out: list[InnerRhymeGroup] = []
    for group in groups:
        by_sig: dict[tuple[str, ...], list[list[RhymeOccurrence]]] = {}
        for o in group.occurrences:
            entries = line_entries.get(o.line_index, [])
            idx = next(
                (i for i, (_, e) in enumerate(entries) if e.word_index == o.word_index),
                None,
            )
            if idx is None or idx == len(entries) - 1:
                continue
            trail = entries[idx + 1 :]
            if len(trail) > _MAX_SPAN_TOKENS - 1:
                continue
            if not all(is_function for is_function, _ in trail):
                continue
            tail_occs = [e for _, e in trail]
            if any((e.line_index, e.word_index) in taken for e in tail_occs):
                continue
            sig = tuple(e.normalized for e in tail_occs)
            by_sig.setdefault(sig, []).append(tail_occs)
        added: list[RhymeOccurrence] = []
        for tails in by_sig.values():
            if len(tails) >= 2:
                for tail_occs in tails:
                    added.extend(tail_occs)
        if not added:
            out.append(group)
            continue
        for e in added:
            taken.add((e.line_index, e.word_index))
        merged = {
            (o.line_index, o.word_index): o for o in [*group.occurrences, *added]
        }
        ordered = sorted(
            merged.values(), key=lambda o: (o.line_index, o.word_index)
        )
        out.append(
            InnerRhymeGroup(
                id=_group_id(language, group.rhyme_type, group.rhyme_key, ordered),
                rhyme_type=group.rhyme_type,
                confidence=group.confidence,
                rhyme_key=group.rhyme_key,
                occurrences=ordered,
            )
        )
    return out


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
    syllables_for: SyllablesFor | None = None,
) -> list[InnerRhymeGroup]:
    """Group rhyming words across ``lines`` into highlight groups.

    ``lines`` is a sequence of ``(line_index, tokens)``; ``line_index`` is echoed
    onto each occurrence (1-based global for drafts, 0 for the single-line
    endpoint). Perfect rhymes take precedence; multisyllabic cadences (single
    words anywhere, plus compound line-ending spans like "countin' this") come
    next; remaining words are matched on the coarser near/slant key. Groups
    that fail anchor pruning, or that span only one distinct line text, are
    dropped.

    ``syllables_for`` overrides the default vowel-phoneme count for languages
    where that count doesn't equal syllables (Spanish diphthongs).
    """
    perfect_fn, near_fn = _KEY_FNS.get(language, (rhyme_key, inner_near_rhyme_key))
    cadence_fn = _CADENCE_KEY_FNS.get(language)
    function_words = _FUNCTION_WORDS.get(language, frozenset())
    min_syllables = _ANCHOR_MIN_SYLLABLES.get(language, _ANCHOR_MIN_SYLLABLES_DEFAULT)
    near_needs_line_final = language in _NEAR_TIER_LINE_FINAL_ONLY

    perfect_buckets_raw: dict[str, list[RhymeOccurrence]] = {}
    # Near/cadence candidates keep their occurrences + key set so we can
    # bucket the ones that survive the earlier tiers.
    near_candidates: list[tuple[set[str], RhymeOccurrence]] = []
    cadence_candidates: list[tuple[set[str], list[RhymeOccurrence]]] = []
    meta: _OccMeta = {}
    # (is_function, occurrence) per line, in order — for function-tail
    # extension after each tier.
    line_entries: dict[int, list[tuple[bool, RhymeOccurrence]]] = {}
    # Normalized text per line, so repeated lines can be recognized as each
    # other in _build_groups.
    line_signatures: dict[int, str] = {}

    for line_index, tokens in lines:
        line_signatures[line_index] = " ".join(t.normalized for t in tokens)
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
                syllables_for(token)
                if syllables_for is not None
                else max(vowel_count(v) for v in variants),
            )
            is_function = token.normalized in function_words
            line_entries.setdefault(line_index, []).append((is_function, occ))
            # Function words highlight only at line end — mid-line
            # "my"/"to"/"the" matches drown the scheme. Heuristic tail
            # guesses never claim a *perfect* match (see
            # ``HeuristicTailVariants``); they stay slant-only.
            if (not is_function or is_line_final) and not isinstance(
                variants, HeuristicTailVariants
            ):
                perfect_keys = {k for v in variants if (k := perfect_fn(v)) is not None}
                for key in perfect_keys:
                    perfect_buckets_raw.setdefault(key, []).append(occ)
            # Function words only count when the sound match is exact — they
            # never seed slant or cadence groups (though they may ride along
            # in a compound span, below).
            if is_function:
                continue
            # Spanish assonance only counts at line endings — see
            # ``_NEAR_TIER_LINE_FINAL_ONLY``.
            if not near_needs_line_final or is_line_final:
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
        line_signatures=line_signatures,
        min_syllables=min_syllables,
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
    perfect_groups = _extend_function_tails(
        perfect_groups, line_entries, language=language, taken=claimed
    )
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
        line_signatures=line_signatures,
        min_syllables=min_syllables,
    )

    claimed.update(
        (o.line_index, o.word_index)
        for group in cadence_groups
        for o in group.occurrences
    )
    cadence_groups = _extend_function_tails(
        cadence_groups, line_entries, language=language, taken=claimed
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
        line_signatures=line_signatures,
        min_syllables=min_syllables,
    )
    claimed.update(
        (o.line_index, o.word_index)
        for group in near_groups
        for o in group.occurrences
    )
    near_groups = _extend_function_tails(
        near_groups, line_entries, language=language, taken=claimed
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
    "spanish_syllables_for",
    "syllables_for_context",
    "HeuristicTailVariants",
    "PhonemesFor",
    "SyllablesFor",
]
