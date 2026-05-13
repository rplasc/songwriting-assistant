import re

from wordfreq import word_frequency

_ALPHA_APOSTROPHE = re.compile(r"^[a-z][a-z']*[a-z]$")

# Words with frequency below this floor are excluded from results entirely.
# Filters surnames, archaic tokens, and invented/nonce words that cmudict
# includes but wordfreq has no evidence for.
_MIN_FREQUENCY: float = 1e-8


def is_clean_word(word: str) -> bool:
    """True for pure-alpha (+ internal apostrophe) words of at least 2 characters.

    Rejects: single letters, hyphened compounds, words with digits or symbols.
    """
    if len(word) < 2:
        return False
    return bool(_ALPHA_APOSTROPHE.match(word))


def rank_candidates(candidates: list[str]) -> list[str]:
    """Return candidates ordered by English word frequency (most common first).

    Also filters:
    - hyphened / symbol-containing tokens (via is_clean_word)
    - words with essentially zero corpus frequency
    """
    scored = [
        (w, word_frequency(w, "en"))
        for w in candidates
        if is_clean_word(w)
    ]
    filtered = [(w, f) for w, f in scored if f >= _MIN_FREQUENCY]
    filtered.sort(key=lambda x: (-x[1], x[0]))
    return [w for w, _ in filtered]


def warm_frequency_cache() -> None:
    """Load wordfreq's data files eagerly at startup to avoid first-request latency."""
    word_frequency("the", "en")
