import re

from app.models.token import Token
from app.repositories.pronunciation_repository import PronunciationRepository

_VOWEL_GROUP = re.compile(r"[aeiouy]+")
_DIPHTHONG_EXCEPTIONS: frozenset[str] = frozenset(
    ("ia", "io", "ua", "ue", "uo", "eo", "ea")
)


def _heuristic_count(word: str) -> int:
    """Vowel-group heuristic for words missing from the dictionary.

    Adjustments:
      - silent trailing `e` (but only when removing it leaves at least one vowel group)
      - trailing `le` after a consonant counts as its own syllable
      - trailing `ed` is mostly silent except after t/d
      - some adjacent-vowel pairs (`ia`, `io`, `ea`...) actually split into two syllables
      - `y` is treated as a vowel
    """
    if not word:
        return 1
    w = word.lower().replace("'", "")
    if not w:
        return 1

    groups = _VOWEL_GROUP.findall(w)
    count = len(groups)

    # Split common di-vowel pairs that read as two syllables (e.g. "lia" in
    # "lyrical-ia", "io" in "radio"). Only add when the pair appears as its own
    # vowel group, not as part of a longer cluster like "eau".
    for pair in _DIPHTHONG_EXCEPTIONS:
        if pair in w and pair in groups:
            count += 1

    # Trailing `e` is usually silent ("bake", "fire") but never drop below 1.
    if w.endswith("e") and not w.endswith("le") and not w.endswith("ee") and count > 1:
        count -= 1

    # `-le` after a consonant ("table", "circle") is its own syllable.
    if w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy":
        count = max(count, 2 if len(groups) >= 1 else 1)

    # `-ed` is silent except after t/d ("rated", "needed").
    if w.endswith("ed") and len(w) > 2 and w[-3] not in "td" and count > 1:
        if "ed" in groups:
            count -= 1

    # `-es` after a sibilant adds a syllable ("buses"); after most consonants
    # it doesn't ("makes"). We bias toward NOT adding because the vowel group
    # heuristic already captured it.

    return max(count, 1)


class SyllableService:
    def __init__(self, repository: PronunciationRepository) -> None:
        self._repository = repository

    def count_word(self, normalized_word: str) -> tuple[int, bool]:
        """Return (count, pronunciation_found). Falls back to a heuristic if unknown."""
        prons = self._repository.lookup(normalized_word)
        if prons:
            return prons[0].syllables, True
        return _heuristic_count(normalized_word), False

    def count_tokens(self, tokens: list[Token]) -> tuple[int, list[tuple[Token, int, bool]]]:
        per_token: list[tuple[Token, int, bool]] = []
        total = 0
        for tok in tokens:
            count, found = self.count_word(tok.normalized)
            per_token.append((tok, count, found))
            total += count
        return total, per_token
