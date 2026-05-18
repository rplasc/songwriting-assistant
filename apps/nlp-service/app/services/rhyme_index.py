import re
from collections.abc import Iterable
from dataclasses import dataclass

from wordfreq import word_frequency

from app.domain.near_rhyme_rules import near_rhyme_key
from app.domain.rhyme_rules import rhyme_key
from app.repositories.pronunciation_repository import PronunciationRepository

_ALPHA_APOSTROPHE = re.compile(r"^[a-z][a-z']*[a-z]$")

# Words with frequency below this floor never enter the rhyme corpus, so they
# never appear as candidates. Filters surnames, archaic tokens, and invented
# words that cmudict includes but wordfreq has no evidence for.
_MIN_FREQUENCY: float = 1e-8


def _is_clean_word(word: str) -> bool:
    if len(word) < 2:
        return False
    return bool(_ALPHA_APOSTROPHE.match(word))


@dataclass(frozen=True, slots=True)
class RhymeEntry:
    word: str
    syllables: int
    frequency: float


class RhymeIndex:
    """Reverse maps of rhyme keys to eligible words, plus a per-word data table.

    The corpus is filtered once at build time: words below the frequency floor
    or failing the alpha-apostrophe check never enter the index, so the rhyme
    request path skips all per-candidate filtering and external lookups.
    """

    def __init__(self, repository: PronunciationRepository) -> None:
        # First pass: collect pronunciations per word so we can compute keys
        # over all variants without rebuilding the entry table.
        prons_by_word: dict[str, list[tuple[str, ...]]] = {}
        first_syllables: dict[str, int] = {}
        for word, pron in repository.iter_entries():
            prons_by_word.setdefault(word, []).append(pron.phonemes)
            if word not in first_syllables:
                first_syllables[word] = pron.syllables

        entries: dict[str, RhymeEntry] = {}
        by_perfect: dict[str, set[str]] = {}
        by_near: dict[str, set[str]] = {}

        for word, prons in prons_by_word.items():
            if not _is_clean_word(word):
                continue
            freq = word_frequency(word, "en")
            if freq < _MIN_FREQUENCY:
                continue
            entries[word] = RhymeEntry(
                word=word,
                syllables=first_syllables[word],
                frequency=freq,
            )
            for phonemes in prons:
                pkey = rhyme_key(phonemes)
                if pkey is not None:
                    by_perfect.setdefault(pkey, set()).add(word)
                nkey = near_rhyme_key(phonemes)
                if nkey is not None:
                    by_near.setdefault(nkey, set()).add(word)

        self._entries = entries
        self._by_perfect = by_perfect
        self._by_near = by_near

    def entry(self, word: str) -> RhymeEntry | None:
        return self._entries.get(word)

    def entries_for(self, words: Iterable[str]) -> list[RhymeEntry]:
        out: list[RhymeEntry] = []
        for w in words:
            e = self._entries.get(w)
            if e is not None:
                out.append(e)
        return out

    def perfect_keys_for_phonemes(self, phonemes_list: list[tuple[str, ...]]) -> set[str]:
        keys: set[str] = set()
        for phonemes in phonemes_list:
            key = rhyme_key(phonemes)
            if key is not None:
                keys.add(key)
        return keys

    def near_keys_for_phonemes(self, phonemes_list: list[tuple[str, ...]]) -> set[str]:
        keys: set[str] = set()
        for phonemes in phonemes_list:
            key = near_rhyme_key(phonemes)
            if key is not None:
                keys.add(key)
        return keys

    def words_for_perfect_keys(self, keys: set[str], exclude: str | None = None) -> set[str]:
        out: set[str] = set()
        for key in keys:
            out.update(self._by_perfect.get(key, ()))
        if exclude is not None:
            out.discard(exclude)
        return out

    def words_for_near_keys(self, keys: set[str], exclude: str | None = None) -> set[str]:
        out: set[str] = set()
        for key in keys:
            out.update(self._by_near.get(key, ()))
        if exclude is not None:
            out.discard(exclude)
        return out
