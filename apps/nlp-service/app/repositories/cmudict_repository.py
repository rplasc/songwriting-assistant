from collections.abc import Iterable

import cmudict

from app.models.pronunciation import Pronunciation
from app.repositories.pronunciation_repository import PronunciationRepository


def _is_vowel(phoneme: str) -> bool:
    return bool(phoneme) and phoneme[-1].isdigit()


def _count_syllables(phonemes: list[str]) -> int:
    return sum(1 for p in phonemes if _is_vowel(p))


def _normalize_key(word: str) -> str:
    # cmudict ships duplicate variants like "fire(1)"; strip the variant suffix.
    base = word.lower()
    paren = base.find("(")
    if paren > 0:
        base = base[:paren]
    return base


class CmuDictRepository(PronunciationRepository):
    def __init__(self) -> None:
        raw = cmudict.dict()
        index: dict[str, list[Pronunciation]] = {}
        for word, pron_lists in raw.items():
            key = _normalize_key(word)
            bucket = index.setdefault(key, [])
            for phonemes in pron_lists:
                pron = Pronunciation(
                    phonemes=tuple(phonemes),
                    syllables=_count_syllables(phonemes),
                )
                if pron not in bucket:
                    bucket.append(pron)
        self._index = index

    def lookup(self, normalized_word: str) -> list[Pronunciation]:
        return list(self._index.get(normalized_word, ()))

    def iter_entries(self) -> Iterable[tuple[str, Pronunciation]]:
        for word, prons in self._index.items():
            for p in prons:
                yield word, p

    def __len__(self) -> int:
        return len(self._index)
