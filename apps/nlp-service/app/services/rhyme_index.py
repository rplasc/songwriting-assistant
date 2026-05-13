from app.domain.rhyme_rules import rhyme_key
from app.repositories.pronunciation_repository import PronunciationRepository


class RhymeIndex:
    """Reverse map of rhyme_key -> set of words sharing that ending."""

    def __init__(self, repository: PronunciationRepository) -> None:
        index: dict[str, set[str]] = {}
        word_keys: dict[str, set[str]] = {}
        for word, pron in repository.iter_entries():
            key = rhyme_key(pron.phonemes)
            if key is None:
                continue
            index.setdefault(key, set()).add(word)
            word_keys.setdefault(word, set()).add(key)
        self._by_key = index
        self._by_word = word_keys

    def candidates_for(self, word: str) -> set[str]:
        keys = self._by_word.get(word, ())
        out: set[str] = set()
        for key in keys:
            out.update(self._by_key.get(key, ()))
        out.discard(word)
        return out

    def keys_for_phonemes(self, phonemes_list: list[tuple[str, ...]]) -> set[str]:
        keys: set[str] = set()
        for phonemes in phonemes_list:
            key = rhyme_key(phonemes)
            if key is not None:
                keys.add(key)
        return keys

    def words_for_keys(self, keys: set[str], exclude: str | None = None) -> set[str]:
        out: set[str] = set()
        for key in keys:
            out.update(self._by_key.get(key, ()))
        if exclude is not None:
            out.discard(exclude)
        return out
