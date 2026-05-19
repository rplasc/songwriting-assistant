import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from wordfreq import word_frequency

from app.domain.near_rhyme_rules import near_rhyme_key
from app.domain.rhyme_rules import family_rhyme_key, rhyme_key
from app.repositories.pronunciation_repository import PronunciationRepository

# Deliberately excludes hyphens: normalize_word accepts "well-known" as a valid
# lookup input, but hyphenated compounds make poor rhyme candidates (the rhyming
# unit is the final component, not the compound). Keeping candidates to plain
# or apostrophised words keeps result quality high without needing a split pass.
_ALPHA_APOSTROPHE = re.compile(r"^[a-z][a-z']*[a-z]$")

# Words with frequency below this floor never enter the rhyme corpus, so they
# never appear as candidates. Filters surnames, archaic tokens, and invented
# words that cmudict includes but wordfreq has no evidence for.
# This constant is imported by ranking_service to derive its log-floor so both
# values stay in sync if the threshold is ever tuned.
CORPUS_FREQ_FLOOR: float = 1e-8


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
        # First pass: collect pronunciations and syllable counts per word so we
        # can compute keys over all variants without rebuilding the entry table.
        prons_by_word: dict[str, list[tuple[str, ...]]] = {}
        syllable_counts: dict[str, list[int]] = {}
        for word, pron in repository.iter_entries():
            prons_by_word.setdefault(word, []).append(pron.phonemes)
            syllable_counts.setdefault(word, []).append(pron.syllables)

        entries: dict[str, RhymeEntry] = {}
        by_perfect: dict[str, set[str]] = {}
        by_family: dict[str, set[str]] = {}
        by_near: dict[str, set[str]] = {}

        for word, prons in prons_by_word.items():
            if not _is_clean_word(word):
                continue
            freq = word_frequency(word, "en")
            if freq < CORPUS_FREQ_FLOOR:
                continue
            # Use the modal syllable count across all pronunciations. For words
            # where pronunciations agree (the common case) this is identical to
            # "first". For heteronyms where one count dominates (e.g. three
            # pronunciations at 3 syllables vs one at 2), it picks the majority.
            # Ties resolve in CMU-insertion order via Counter's stability.
            counts = syllable_counts[word]
            modal_syllables = Counter(counts).most_common(1)[0][0]
            entries[word] = RhymeEntry(
                word=word,
                syllables=modal_syllables,
                frequency=freq,
            )
            for phonemes in prons:
                pkey = rhyme_key(phonemes)
                if pkey is not None:
                    by_perfect.setdefault(pkey, set()).add(word)
                fkey = family_rhyme_key(phonemes)
                if fkey is not None:
                    by_family.setdefault(fkey, set()).add(word)
                nkey = near_rhyme_key(phonemes)
                if nkey is not None:
                    by_near.setdefault(nkey, set()).add(word)

        self._entries = entries
        self._by_perfect = by_perfect
        self._by_family = by_family
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

    def family_keys_for_phonemes(self, phonemes_list: list[tuple[str, ...]]) -> set[str]:
        keys: set[str] = set()
        for phonemes in phonemes_list:
            key = family_rhyme_key(phonemes)
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

    def words_for_family_keys(self, keys: set[str], exclude: str | None = None) -> set[str]:
        out: set[str] = set()
        for key in keys:
            out.update(self._by_family.get(key, ()))
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


def warm_frequency_cache() -> None:
    """Load wordfreq's data files eagerly at startup to avoid first-request latency."""
    word_frequency("the", "en")
