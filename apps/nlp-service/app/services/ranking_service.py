import re

_ALPHA_HYPHEN_APOSTROPHE = re.compile(r"^[a-z][a-z'\-]*[a-z]?$")


def is_clean_word(word: str) -> bool:
    """Filter abbreviations, single-letter entries, and punctuation-heavy variants."""
    if len(word) < 2:
        return False
    return bool(_ALPHA_HYPHEN_APOSTROPHE.match(word))


def rank_candidates(candidates: list[str]) -> list[str]:
    """Stable ordering: shorter words first, then alphabetic."""
    filtered = [w for w in candidates if is_clean_word(w)]
    filtered.sort(key=lambda w: (len(w), w))
    return filtered
