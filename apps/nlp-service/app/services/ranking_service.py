import heapq
import math
from collections.abc import Iterable
from dataclasses import dataclass

from wordfreq import word_frequency

from app.domain.languages.base import LanguageEngine
from app.services.rhyme_index import CORPUS_FREQ_FLOOR, RhymeEntry

# Floor used to compute the frequency component of the score.
# Derived from CORPUS_FREQ_FLOOR so the corpus filter and the score formula
# always share the same boundary: a word just above the floor scores near 0.0.
_FREQ_LOG_FLOOR: float = math.log10(CORPUS_FREQ_FLOOR)  # -8.0 at 1e-8
_FREQ_LOG_CEIL: float = -2.0

# Score weights — kept transparent and tunable. Final score is clamped to [0, 1].
_BASE_PERFECT: float = 0.80
_BASE_FAMILY: float = 0.68
_BASE_NEAR: float = 0.55
_FREQ_WEIGHT: float = 0.20
_SYLLABLE_BONUS: float = 0.05
_STRESS_BONUS: float = 0.03

# Spanish consonant rhyme is the analog of the English perfect tier (full
# phonetic match from the stressed vowel onward). Assonant is a legitimate
# Spanish rhyme type — not slant — so it scores above English's "near".
_BASE_CONSONANT: float = 0.80
_BASE_ASSONANT: float = 0.62

# Multisyllabic matches are strictly stronger than single-syllable perfect
# matches (more shared phonemes), so they sit slightly above perfect/consonant.
_BASE_MULTISYLLABIC: float = 0.85

# Scale a small bonus by the length of the shared stressed tail.
# Fires only when BOTH query and candidate carry a multisyllabic key, so it
# never affects single-vowel-tail queries like "cat" or "fire". The
# normaliser saturates around 4 vowels + 4 consonants of shared tail.
_MULTISYLLABIC_LEN_BONUS: float = 0.05
_MULTISYLLABIC_LEN_NORMALISER: int = 8

_BASE_BY_TYPE: dict[str, float] = {
    "perfect": _BASE_PERFECT,
    "family": _BASE_FAMILY,
    "near": _BASE_NEAR,
    "consonant": _BASE_CONSONANT,
    "assonant": _BASE_ASSONANT,
    "multisyllabic": _BASE_MULTISYLLABIC,
}

# Editorial penalties for low-value rhymes.
_INFLECTION_PENALTY: float = 0.20
_SAME_STEM_PENALTY: float = 0.10


def _frequency_component(freq: float) -> float:
    if freq <= 0:
        return 0.0
    log_freq = math.log10(freq)
    if log_freq <= _FREQ_LOG_FLOOR:
        return 0.0
    if log_freq >= _FREQ_LOG_CEIL:
        return 1.0
    return (log_freq - _FREQ_LOG_FLOOR) / (_FREQ_LOG_CEIL - _FREQ_LOG_FLOOR)


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    word: str
    score: float
    frequency: float
    syllables: int


def score_entries(
    entries: Iterable[RhymeEntry],
    *,
    query: str,
    rhyme_type: str,
    limit: int,
    query_syllables: int | None = None,
    query_multisyllabic_len: int | None = None,
    engine: LanguageEngine,
) -> list[ScoredCandidate]:
    """Score pre-filtered rhyme entries and return the top `limit` ordered.

    Inputs are already filtered for word shape and minimum frequency by the
    index, so this function does no I/O and no string filtering — only math
    and short string comparisons. Signals:

      1. base score by rhyme strength (perfect > family > near)
      2. frequency component (commonness as a proxy for naturalness)
      3. syllable proximity bonus
      4. stress-position match bonus (engine-provided; None disables it)
      5. editorial penalties for inflection and same-stem rhymes (engine-delegated)

    Top-K is extracted with `heapq.nsmallest`, which is O(n log k) vs the
    O(n log n) of a full sort. For high-candidate words ("time" has 1000+
    near candidates) with limit=25 this is the dominant hot-path win.

    Per-candidate work is kept tight: the inflection-penalty set is built
    once via :meth:`LanguageEngine.inflection_forms` and queried with O(1)
    set membership, and the heap stores natively-ordered tuples so
    ``ScoredCandidate`` instances are only materialised for the survivors.
    """
    base = _BASE_BY_TYPE.get(rhyme_type, _BASE_NEAR)
    query_stress = engine.stress_signature(query)
    inflection_set = engine.inflection_forms(query)
    # Tuples sort lexicographically: (-score, -freq, word, ...). The trailing
    # score/syllables fields are payload — they don't affect ordering because
    # the leading triple uniquely orders any pair of entries.
    items: list[tuple[float, float, str, float, int]] = []
    for e in entries:
        word = e.word
        score = base + _FREQ_WEIGHT * _frequency_component(e.frequency)
        if query_syllables is not None and e.syllables == query_syllables:
            score += _SYLLABLE_BONUS
        if query_stress is not None and e.stress_class == query_stress:
            score += _STRESS_BONUS
        if query_multisyllabic_len and e.multisyllabic_tail_phonemes:
            shared = min(query_multisyllabic_len, e.multisyllabic_tail_phonemes)
            score += _MULTISYLLABIC_LEN_BONUS * min(
                shared / _MULTISYLLABIC_LEN_NORMALISER, 1.0
            )
        if word in inflection_set:
            score -= _INFLECTION_PENALTY
        elif engine.shares_stem(query, word):
            score -= _SAME_STEM_PENALTY
        if score < 0.0:
            score = 0.0
        elif score > 1.0:
            score = 1.0
        items.append((-score, -e.frequency, word, score, e.syllables))

    if limit >= len(items):
        items.sort()
        top = items
    else:
        top = heapq.nsmallest(limit, items)
    return [
        ScoredCandidate(word=w, score=s, frequency=-neg_freq, syllables=syl)
        for (_neg_score, neg_freq, w, s, syl) in top
    ]


