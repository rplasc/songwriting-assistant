"""Spanish morphological inflection detection.

Used by SpanishEngine.is_same_stem_inflection to penalise same-root verb
conjugations and noun/adjective inflections in rhyme ranking.  Two words that
share a stem but differ only in grammatical ending feel weak as rhyme pairs in
lyrics (cantaba / cantamos sound like the same word, not a real rhyme).

Strategy
--------
We try each known ending for the query to recover a putative stem, then check
whether the candidate equals that stem + a different ending in the same family.
A minimum stem length of 3 characters prevents noise on very short words.

Only the most common paradigm endings are listed — enough to catch the dominant
cases without becoming a full morphological analyser.
"""

from __future__ import annotations

_MIN_STEM = 3

# ---------------------------------------------------------------------------
# -ar verb endings
# ---------------------------------------------------------------------------
_AR_ENDINGS: frozenset[str] = frozenset(
    (
        # infinitive
        "ar",
        # present indicative
        "o", "as", "a", "amos", "áis", "an",
        # imperfect indicative
        "aba", "abas", "aba", "ábamos", "abais", "aban",
        # preterite indicative
        "é", "aste", "ó", "amos", "asteis", "aron",
        # future indicative
        "aré", "arás", "ará", "aremos", "aréis", "arán",
        # conditional
        "aría", "arías", "aría", "aríamos", "aríais", "arían",
        # present subjunctive
        "e", "es", "e", "emos", "éis", "en",
        # imperfect subjunctive (-ra form)
        "ara", "aras", "ara", "áramos", "arais", "aran",
        # imperative (informal)
        "a", "ad",
        # participle / gerund
        "ado", "ada", "ados", "adas", "ando",
    )
)

# ---------------------------------------------------------------------------
# -er verb endings
# ---------------------------------------------------------------------------
_ER_ENDINGS: frozenset[str] = frozenset(
    (
        # infinitive
        "er",
        # present indicative
        "o", "es", "e", "emos", "éis", "en",
        # imperfect indicative
        "ía", "ías", "ía", "íamos", "íais", "ían",
        # preterite indicative
        "í", "iste", "ió", "imos", "isteis", "ieron",
        # future indicative
        "eré", "erás", "erá", "eremos", "eréis", "erán",
        # conditional
        "ería", "erías", "ería", "eríamos", "eríais", "erían",
        # present subjunctive
        "a", "as", "a", "amos", "áis", "an",
        # imperfect subjunctive (-ra form)
        "iera", "ieras", "iera", "iéramos", "ierais", "ieran",
        # imperative (informal)
        "e", "ed",
        # participle / gerund
        "ido", "ida", "idos", "idas", "iendo",
    )
)

# ---------------------------------------------------------------------------
# -ir verb endings  (future/conditional use ir- root)
# ---------------------------------------------------------------------------
_IR_ENDINGS: frozenset[str] = frozenset(
    (
        # infinitive
        "ir",
        # present indicative (note: -ir verbs use -es/-e/-en, not -es/-e/-en like -er)
        "o", "es", "e", "imos", "ís", "en",
        # imperfect indicative (same as -er)
        "ía", "ías", "ía", "íamos", "íais", "ían",
        # preterite indicative
        "í", "iste", "ió", "imos", "isteis", "ieron",
        # future indicative
        "iré", "irás", "irá", "iremos", "iréis", "irán",
        # conditional
        "iría", "irías", "iría", "iríamos", "iríais", "irían",
        # present subjunctive
        "a", "as", "a", "amos", "áis", "an",
        # imperfect subjunctive (-ra form)
        "iera", "ieras", "iera", "iéramos", "ierais", "ieran",
        # imperative (informal)
        "e", "id",
        # participle / gerund
        "ido", "ida", "idos", "idas", "iendo",
    )
)

# All verb endings that can terminate an infinitive, used to detect the verb family.
_AR_INFINITIVE_ENDINGS: tuple[str, ...] = ("ar",)
_ER_INFINITIVE_ENDINGS: tuple[str, ...] = ("er",)
_IR_INFINITIVE_ENDINGS: tuple[str, ...] = ("ir",)

# Map from each possible query ending to the full paradigm set it belongs to.
# Built once at module load.
_PARADIGM_BY_ENDING: dict[str, frozenset[str]] = {}
for _e in _AR_ENDINGS:
    _PARADIGM_BY_ENDING.setdefault(_e, frozenset()).union  # pre-register key
for _e in _AR_ENDINGS:
    prev = _PARADIGM_BY_ENDING.get(_e, frozenset())
    _PARADIGM_BY_ENDING[_e] = prev | _AR_ENDINGS
for _e in _ER_ENDINGS:
    prev = _PARADIGM_BY_ENDING.get(_e, frozenset())
    _PARADIGM_BY_ENDING[_e] = prev | _ER_ENDINGS
for _e in _IR_ENDINGS:
    prev = _PARADIGM_BY_ENDING.get(_e, frozenset())
    _PARADIGM_BY_ENDING[_e] = prev | _IR_ENDINGS

# Noun/adjective endings for pluralisation and gender pairs.
_NOUN_ADJ_ENDINGS: frozenset[str] = frozenset(("s", "es", "a", "o", "as", "os"))

_VOWELS: frozenset[str] = frozenset("aeiouáéíóú")

# Pre-sorted (descending length) tuple of all verb endings — built once at
# module load so per-query callers don't pay the sort cost.
_ALL_VERB_ENDINGS_DESC: tuple[str, ...] = tuple(
    sorted(set(_AR_ENDINGS) | set(_ER_ENDINGS) | set(_IR_ENDINGS), key=len, reverse=True)
)
_NOUN_ADJ_ENDINGS_DESC: tuple[str, ...] = tuple(
    sorted(_NOUN_ADJ_ENDINGS, key=len, reverse=True)
)


def _strip_ending(word: str, ending: str) -> str | None:
    """Return the stem if word ends with ending and stem is long enough."""
    if word.endswith(ending):
        stem = word[: len(word) - len(ending)]
        if len(stem) >= _MIN_STEM:
            return stem
    return None


def inflection_forms(query: str) -> frozenset[str]:
    """Return the full set of candidate words that should be treated as
    same-stem inflections of ``query``.

    This is the materialised form of :func:`is_same_stem_inflection`: building
    the set once per query lets the ranking loop replace per-candidate string
    work with O(1) ``in`` checks. The two helpers share the same generation
    logic so their answers cannot drift.
    """
    if not query:
        return frozenset()

    forms: set[str] = set()

    # --- Verb paradigm forms ---
    for ending in _ALL_VERB_ENDINGS_DESC:
        stem = _strip_ending(query, ending)
        if stem is None:
            continue
        paradigm = _PARADIGM_BY_ENDING.get(ending)
        if paradigm is None:
            continue
        for cand_ending in paradigm:
            if cand_ending != ending:
                forms.add(stem + cand_ending)

    # --- Noun/adjective gender + plural pairs ---
    for ending in _NOUN_ADJ_ENDINGS_DESC:
        stem = _strip_ending(query, ending)
        if stem is None:
            continue
        for cand_ending in _NOUN_ADJ_ENDINGS:
            if cand_ending != ending:
                forms.add(stem + cand_ending)

    # Bare-stem case: query itself is the stem.
    if len(query) >= _MIN_STEM:
        for cand_ending in _NOUN_ADJ_ENDINGS_DESC:
            forms.add(query + cand_ending)

    forms.discard(query)
    return frozenset(forms)


def is_same_stem_inflection(query: str, candidate: str) -> bool:
    """Return True if candidate is a different inflected form of the same verb or
    noun/adjective root as query.

    Delegates to :func:`inflection_forms` so the predicate and set match
    exactly. Cheap initial filters short-circuit obvious non-matches before
    paying the set-build cost.
    """
    if not query or not candidate or query == candidate:
        return False
    if not candidate.startswith(query[0]):
        return False
    return candidate in inflection_forms(query)
