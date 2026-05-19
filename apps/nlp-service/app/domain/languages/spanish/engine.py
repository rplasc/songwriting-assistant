"""SpanishEngine — wires the Spanish modules into the LanguageEngine interface."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wordfreq import word_frequency

from app.domain.languages.base import CandidateTier, KeySpec, LanguageEngine
from app.domain.languages.spanish.normalization import normalize_word
from app.domain.languages.spanish.rhyme_rules import (
    assonant_rhyme_key,
    consonant_rhyme_key,
)
from app.domain.languages.spanish.syllabification import syllabify
from app.models.token import Token

if TYPE_CHECKING:
    from app.services.rhyme_index import RhymeIndex


# Mirrors the English ``_is_clean_word`` shape filter, widened for Spanish:
# accepts ñ, ü, and accented vowels. Hyphenated forms are excluded — the
# rhyming unit would be the last component, not the compound, which makes
# them poor index candidates.
_SPANISH_WORD_RE = re.compile(r"^[a-záéíóúñü][a-záéíóúñü']*[a-záéíóúñü]$")


def _spanish_tokenize_line(line: str) -> list[Token]:
    """Whitespace split + Spanish normalize. Mirrors the English shape so the
    SyllableService can count tokens uniformly."""
    if not line:
        return []
    out: list[Token] = []
    for raw in line.split():
        norm = normalize_word(raw)
        if norm is None:
            continue
        out.append(Token(text=raw, normalized=norm))
    return out


class SpanishEngine(LanguageEngine):
    code = "es"
    supported_modes = ("consonant", "assonant")
    default_mode = "consonant"
    key_specs = (
        KeySpec(name="consonant", fn=consonant_rhyme_key),
        KeySpec(name="assonant", fn=assonant_rhyme_key),
    )
    match_reasons = {
        "consonant": "shared ending from stressed vowel",
        "assonant": "shared vowel pattern from stressed vowel",
    }

    def normalize_word(self, text: str | None) -> str | None:
        return normalize_word(text)

    def tokenize_line(self, line: str) -> list[Token]:
        return _spanish_tokenize_line(line)

    def heuristic_syllable_count(self, word: str) -> int:
        # Spanish syllabification is rule-based and exact, so the rule is
        # used directly rather than as a fallback after a dictionary miss.
        syllables, _ = syllabify(word)
        return max(len(syllables), 1)

    def frequency(self, word: str) -> float:
        return word_frequency(word, "es")

    def is_corpus_eligible_word(self, word: str) -> bool:
        if len(word) < 2:
            return False
        return bool(_SPANISH_WORD_RE.match(word))

    def candidate_tiers(
        self,
        index: "RhymeIndex",
        normalized: str,
        phonemes_list: list[tuple[str, ...]],
        mode: str,
        query_syllables: int,
    ) -> list[CandidateTier]:
        consonant_keys = index.keys_for("consonant", phonemes_list)
        assonant_keys = index.keys_for("assonant", phonemes_list)

        consonant_words = index.words_for(
            "consonant", consonant_keys, exclude=normalized
        )
        # Assonant rhymes are defined as vowel-only matches that are NOT
        # full consonant matches. Subtracting keeps the two tiers disjoint
        # and matches how Spanish poetry treats the distinction.
        assonant_words = (
            index.words_for("assonant", assonant_keys, exclude=normalized)
            - consonant_words
        )

        if mode == "assonant":
            return [CandidateTier(name="assonant", words=assonant_words)]
        # mode == "consonant" — cascade consonant → assonant.
        return [
            CandidateTier(name="consonant", words=consonant_words),
            CandidateTier(name="assonant", words=assonant_words),
        ]
