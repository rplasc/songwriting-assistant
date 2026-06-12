from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from wordfreq import word_frequency

from app.domain.languages.base import LanguageEngine
from app.domain.rhyme.multisyllabic_rules import multisyllabic_rhyme_key
from app.repositories.pronunciation_repository import PronunciationRepository

# Words with frequency below this floor never enter the rhyme corpus, so they
# never appear as candidates. Filters surnames, archaic tokens, and invented
# words that the source lexicon includes but wordfreq has no evidence for.
# This constant is imported by ranking_service to derive its log-floor so both
# values stay in sync if the threshold is ever tuned.
CORPUS_FREQ_FLOOR: float = 1e-8


@dataclass(frozen=True, slots=True)
class RhymeEntry:
    word: str
    syllables: int
    frequency: float
    # Length (in phonemes) of the entry's multisyllabic tail.
    # Zero for words with no multisyllabic key (fewer than two vowels after
    # the last stressed vowel). Used by ranking_service to reward longer
    # shared stressed tails — see _MULTISYLLABIC_LEN_BONUS.
    multisyllabic_tail_phonemes: int = 0
    # Prosodic stress class ("aguda"/"llana"/"esdrujula" for Spanish), or
    # None for engines that don't use stress-position ranking (English).
    # Precomputed at index build so score_entries can compare it per
    # candidate without re-running syllabification on every call.
    stress_class: str | None = None


class RhymeIndex:
    """Reverse maps of named rhyme-key slots to eligible words, plus a per-word
    data table.

    Slots are defined by the LanguageEngine via ``engine.key_specs`` — English
    declares ``perfect``/``family``/``near``; Spanish declares
    ``consonant``/``assonant``. The index is otherwise language-agnostic.

    The corpus is filtered once at build time: words below the frequency floor
    or failing the engine's shape check never enter the index, so the rhyme
    request path skips all per-candidate filtering and external lookups.
    """

    def __init__(
        self,
        repository: PronunciationRepository,
        engine: LanguageEngine,
    ) -> None:
        self._engine = engine

        # First pass: collect pronunciations and syllable counts per word so we
        # can compute keys over all variants without rebuilding the entry table.
        prons_by_word: dict[str, list[tuple[str, ...]]] = {}
        syllable_counts: dict[str, list[int]] = {}
        for word, pron in repository.iter_entries():
            prons_by_word.setdefault(word, []).append(pron.phonemes)
            syllable_counts.setdefault(word, []).append(pron.syllables)

        entries: dict[str, RhymeEntry] = {}
        by_slot: dict[str, dict[str, set[str]]] = {
            spec.name: {} for spec in engine.key_specs
        }

        for word, prons in prons_by_word.items():
            if not engine.is_corpus_eligible_word(word):
                continue
            freq = engine.frequency(word)
            if freq < CORPUS_FREQ_FLOOR:
                continue
            # Use the modal syllable count across all pronunciations. For words
            # where pronunciations agree (the common case) this is identical to
            # "first". For heteronyms where one count dominates (e.g. three
            # pronunciations at 3 syllables vs one at 2), it picks the majority.
            counts = syllable_counts[word]
            modal_syllables = Counter(counts).most_common(1)[0][0]
            # Compute the longest multisyllabic tail across pronunciation
            # variants. Heteronyms can have one variant that qualifies and
            # another that doesn't (e.g. unstressed vs stressed second
            # syllable); the longer tail is the more honest signal because
            # the engine surfaces the matching variant at lookup time.
            multi_len = 0
            for phonemes in prons:
                key = multisyllabic_rhyme_key(phonemes)
                if key is not None:
                    multi_len = max(multi_len, len(key.split("_")))
            entries[word] = RhymeEntry(
                word=word,
                syllables=modal_syllables,
                frequency=freq,
                multisyllabic_tail_phonemes=multi_len,
                stress_class=engine.stress_signature(word),
            )
            for phonemes in prons:
                for spec in engine.key_specs:
                    key = spec.fn(phonemes)
                    if key is not None:
                        by_slot[spec.name].setdefault(key, set()).add(word)

        self._entries = entries
        self._by_slot = by_slot

    def entry(self, word: str) -> RhymeEntry | None:
        return self._entries.get(word)

    def entries_for(self, words: Iterable[str]) -> list[RhymeEntry]:
        out: list[RhymeEntry] = []
        for w in words:
            e = self._entries.get(w)
            if e is not None:
                out.append(e)
        return out

    def keys_for(
        self, slot: str, phonemes_list: Iterable[tuple[str, ...]]
    ) -> set[str]:
        try:
            spec_fn = next(
                spec.fn for spec in self._engine.key_specs if spec.name == slot
            )
        except StopIteration as exc:
            raise KeyError(f"unknown rhyme-key slot '{slot}'") from exc
        keys: set[str] = set()
        for phonemes in phonemes_list:
            key = spec_fn(phonemes)
            if key is not None:
                keys.add(key)
        return keys

    def words_for(
        self,
        slot: str,
        keys: Iterable[str],
        exclude: str | None = None,
    ) -> set[str]:
        slot_map = self._by_slot.get(slot)
        if slot_map is None:
            raise KeyError(f"unknown rhyme-key slot '{slot}'")
        out: set[str] = set()
        for key in keys:
            bucket = slot_map.get(key)
            if bucket is not None:
                out.update(bucket)
        if exclude is not None:
            out.discard(exclude)
        return out

    def word_count(self) -> int:
        return len(self._entries)


def warm_frequency_cache() -> None:
    """Load wordfreq's data files eagerly at startup to avoid first-request latency."""
    word_frequency("the", "en")
    word_frequency("el", "es")
