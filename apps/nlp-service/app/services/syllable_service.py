import re

from app.models.token import Token
from app.repositories.pronunciation_repository import PronunciationRepository

_VOWEL_GROUP = re.compile(r"[aeiouy]+")


def _heuristic_count(word: str) -> int:
    """Vowel-group heuristic for words missing from the dictionary.

    Adjustments:
      - silent trailing `e`
      - trailing `le` after a consonant counts once
      - `y` is treated as a vowel
    """
    if not word:
        return 1
    w = word.lower()
    groups = _VOWEL_GROUP.findall(w)
    count = len(groups)
    if w.endswith("e") and not w.endswith("le") and count > 1:
        count -= 1
    if w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy":
        count = max(count, 1)
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
