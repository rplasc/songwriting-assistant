import math
from collections.abc import Iterable
from dataclasses import dataclass

from wordfreq import word_frequency

from app.services.rhyme_index import RhymeEntry

# Floor used to compute the frequency component of the score. log10(1e-8)=-8,
# log10(1e-2)=-2; we map that range to [0, 1].
_FREQ_LOG_FLOOR: float = -8.0
_FREQ_LOG_CEIL: float = -2.0

# Score weights — kept transparent and tunable. Final score is clamped to [0, 1].
_BASE_PERFECT: float = 0.80
_BASE_NEAR: float = 0.55
_FREQ_WEIGHT: float = 0.20
_SYLLABLE_BONUS: float = 0.05

# Editorial penalties for low-value rhymes.
_INFLECTION_PENALTY: float = 0.20
_SAME_STEM_PENALTY: float = 0.10

_INFLECTION_SUFFIXES: frozenset[str] = frozenset(
    ("s", "es", "ed", "ing", "er", "est")
)


def _frequency_component(freq: float) -> float:
    if freq <= 0:
        return 0.0
    log_freq = math.log10(freq)
    if log_freq <= _FREQ_LOG_FLOOR:
        return 0.0
    if log_freq >= _FREQ_LOG_CEIL:
        return 1.0
    return (log_freq - _FREQ_LOG_FLOOR) / (_FREQ_LOG_CEIL - _FREQ_LOG_FLOOR)


def _is_same_stem_inflection(query: str, candidate: str) -> bool:
    """True if candidate looks like query + a common English inflection.

    Covers four patterns:
      - plain suffix:           walk  -> walked, walks, walking
      - doubled consonant:      run   -> running, runs (run+ning, run+s)
      - silent-e drop:          make  -> making, dance -> danced
      - y -> i swap:            try   -> tries, cry -> cried
    Same-stem rhymes feel weak in lyrics and should rank lower.
    """
    if not query or candidate == query or not candidate.startswith(query[:1]):
        return False

    if candidate.startswith(query) and candidate[len(query) :] in _INFLECTION_SUFFIXES:
        return True

    if (
        len(query) >= 2
        and query[-1] not in "aeiouy"
        and candidate.startswith(query + query[-1])
        and candidate[len(query) + 1 :] in _INFLECTION_SUFFIXES
    ):
        return True

    if query.endswith("e") and candidate.startswith(query[:-1]):
        if candidate[len(query) - 1 :] in _INFLECTION_SUFFIXES:
            return True

    if query.endswith("y") and len(query) >= 2 and query[-2] not in "aeiou":
        if candidate.startswith(query[:-1] + "i"):
            if candidate[len(query) :] in _INFLECTION_SUFFIXES:
                return True

    return False


def _shares_stem(query: str, candidate: str, min_stem: int = 4) -> bool:
    if len(query) < min_stem or len(candidate) < min_stem:
        return False
    shared = 0
    for a, b in zip(query, candidate):
        if a != b:
            break
        shared += 1
    return shared >= min_stem and shared >= len(query) - 1


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
    query_syllables: int | None = None,
) -> list[ScoredCandidate]:
    """Score and order pre-filtered rhyme entries.

    Inputs are already filtered for word shape and minimum frequency by the
    index, so this function does no I/O and no string filtering — only math
    and short string comparisons. Signals:

      1. base score by rhyme strength (perfect > near)
      2. frequency component (commonness as a proxy for naturalness)
      3. syllable proximity bonus
      4. editorial penalties for inflection and same-stem rhymes
    """
    base = _BASE_PERFECT if rhyme_type == "perfect" else _BASE_NEAR
    out: list[ScoredCandidate] = []
    for e in entries:
        score = base + _FREQ_WEIGHT * _frequency_component(e.frequency)
        if query_syllables is not None and e.syllables == query_syllables:
            score += _SYLLABLE_BONUS
        if _is_same_stem_inflection(query, e.word):
            score -= _INFLECTION_PENALTY
        elif _shares_stem(query, e.word):
            score -= _SAME_STEM_PENALTY
        if score < 0.0:
            score = 0.0
        elif score > 1.0:
            score = 1.0
        out.append(
            ScoredCandidate(
                word=e.word,
                score=score,
                frequency=e.frequency,
                syllables=e.syllables,
            )
        )
    out.sort(key=lambda c: (-c.score, -c.frequency, c.word))
    return out


def warm_frequency_cache() -> None:
    """Load wordfreq's data files eagerly at startup to avoid first-request latency."""
    word_frequency("the", "en")
