"""English engine: thin wrapper that exposes the existing English logic
(normalization, tokenization, rhyme keys, heuristic G2P/syllables) through
the LanguageEngine interface. No new behavior; the rhyme cascade and
fallback below replicate the pre-refactor RhymeService exactly so cached
English results do not drift."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wordfreq import word_frequency

from app.domain.heuristic_g2p import heuristic_phoneme_tails
from app.domain.languages.base import CandidateTier, KeySpec, LanguageEngine
from app.domain.near_rhyme_rules import near_rhyme_key
from app.domain.normalization import normalize_word
from app.domain.rhyme_rules import family_rhyme_key, rhyme_key
from app.domain.tokenization import tokenize_line
from app.models.token import Token

if TYPE_CHECKING:
    from app.services.rhyme_index import RhymeIndex


_VOWEL_LETTERS: frozenset[str] = frozenset("aeiouy")

_INFLECTION_SUFFIXES: frozenset[str] = frozenset(("s", "es", "ed", "ing", "er", "est"))


def _en_is_same_stem_inflection(query: str, candidate: str) -> bool:
    """True if candidate looks like query + a common English inflection.

    Covers four patterns:
      - plain suffix:           walk  -> walked, walks, walking
      - doubled consonant:      run   -> running (run+ning)
      - silent-e drop:          make  -> making, dance -> danced
      - y -> i swap:            try   -> tries, cry -> cried
    """
    if not query or candidate == query or not candidate.startswith(query[:1]):
        return False
    if candidate.startswith(query) and candidate[len(query):] in _INFLECTION_SUFFIXES:
        return True
    if (
        len(query) >= 2
        and query[-1] not in "aeiouy"
        and candidate.startswith(query + query[-1])
        and candidate[len(query) + 1:] in _INFLECTION_SUFFIXES
    ):
        return True
    if query.endswith("e") and candidate.startswith(query[:-1]):
        if candidate[len(query) - 1:] in _INFLECTION_SUFFIXES:
            return True
    if query.endswith("y") and len(query) >= 2 and query[-2] not in "aeiou":
        if candidate.startswith(query[:-1] + "i"):
            if candidate[len(query):] in _INFLECTION_SUFFIXES:
                return True
    return False


def _english_heuristic_syllable_count(word: str) -> int:
    # Local re-implementation of the existing English heuristic so the
    # SyllableService can call it via the engine without circular-importing
    # SyllableService. Mirrors app.services.syllable_service._heuristic_count.
    import re

    if not word:
        return 1
    w = word.lower().replace("'", "")
    if not w:
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    count = len(groups)
    for pair in ("ia", "io", "ua", "ue", "uo", "eo", "ea"):
        if pair in w and pair in groups:
            count += 1
    if w.endswith("e") and not w.endswith("le") and not w.endswith("ee") and count > 1:
        count -= 1
    if w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy":
        count = max(count, 2 if len(groups) >= 1 else 1)
    if w.endswith("ed") and len(w) > 2 and w[-3] not in "td" and count > 1:
        if "ed" in groups:
            count -= 1
    return max(count, 1)


class EnglishEngine(LanguageEngine):
    code = "en"
    supported_modes = ("perfect", "near")
    default_mode = "perfect"
    key_specs = (
        KeySpec(name="perfect", fn=rhyme_key),
        KeySpec(name="family", fn=family_rhyme_key),
        KeySpec(name="near", fn=near_rhyme_key),
    )
    match_reasons = {
        "perfect": "shared stressed ending",
        "family": "shared trailing syllable",
        "near": "shared vowel with similar consonants",
    }

    def normalize_word(self, text: str | None) -> str | None:
        return normalize_word(text)

    def tokenize_line(self, line: str) -> list[Token]:
        return tokenize_line(line)

    def heuristic_syllable_count(self, word: str) -> int:
        return _english_heuristic_syllable_count(word)

    def frequency(self, word: str) -> float:
        return word_frequency(word, "en")

    def is_corpus_eligible_word(self, word: str) -> bool:
        import re

        if len(word) < 2:
            return False
        return bool(re.match(r"^[a-z][a-z']*[a-z]$", word))

    def candidate_tiers(
        self,
        index: "RhymeIndex",
        normalized: str,
        phonemes_list: list[tuple[str, ...]],
        mode: str,
        query_syllables: int,
    ) -> list[CandidateTier]:
        perfect_keys = index.keys_for("perfect", phonemes_list)
        family_keys = index.keys_for("family", phonemes_list)
        near_keys = index.keys_for("near", phonemes_list)

        perfect_words = index.words_for("perfect", perfect_keys, exclude=normalized)
        family_words = (
            index.words_for("family", family_keys, exclude=normalized) - perfect_words
        )
        near_words = (
            index.words_for("near", near_keys, exclude=normalized)
            - perfect_words
            - family_words
        )

        if mode == "near":
            return [CandidateTier(name="near", words=near_words)]
        # mode == "perfect" — tiered cascade.
        return [
            CandidateTier(name="perfect", words=perfect_words),
            CandidateTier(name="family", words=family_words),
            CandidateTier(name="near", words=near_words),
        ]

    def is_same_stem_inflection(self, query: str, candidate: str) -> bool:
        return _en_is_same_stem_inflection(query, candidate)

    def heuristic_candidates(
        self,
        index: "RhymeIndex",
        normalized: str,
    ) -> list[CandidateTier]:
        """English-only fallback: spelling-derived phoneme tails → family-tier matches."""
        tails = heuristic_phoneme_tails(normalized)
        if not tails:
            return []
        perfect_keys = index.keys_for("perfect", list(tails))
        family_keys = index.keys_for("family", list(tails))
        words = index.words_for(
            "perfect", perfect_keys, exclude=normalized
        ) | index.words_for("family", family_keys, exclude=normalized)
        if not words:
            return []
        return [CandidateTier(name="family", words=words)]
