"""SpanishEngine — wires the Spanish modules into the LanguageEngine interface."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wordfreq import word_frequency

from app.domain.languages.base import CandidateTier, KeySpec, LanguageEngine
from app.domain.languages.spanish.data.pr_slang import PR_SLANG
from app.domain.languages.spanish.function_words import SPANISH_FUNCTION_WORDS
from app.domain.languages.spanish.inflection import (
    inflection_forms as _es_inflection_forms,
    is_same_stem_inflection as _es_is_same_stem_inflection,
)
from app.domain.languages.spanish.normalization import normalize_word
from app.domain.languages.spanish.rhyme_rules import (
    assonant_rhyme_key,
    consonant_rhyme_key,
)
from app.domain.languages.spanish.stress import stress_signature as _es_stress_signature
from app.domain.languages.spanish.syllabification import syllabify
from app.domain.rhyme.multisyllabic_rules import multisyllabic_rhyme_key
from app.domain.tokenization import iter_word_spans
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
    SyllableService can count tokens uniformly. Word index and character offsets
    are populated for inner-rhyme highlighting."""
    if not line:
        return []
    out: list[Token] = []
    for raw, char_start, char_end in iter_word_spans(line):
        norm = normalize_word(raw)
        if norm is None:
            continue
        out.append(
            Token(
                text=raw,
                normalized=norm,
                index=len(out),
                char_start=char_start,
                char_end=char_end,
            )
        )
    return out


class SpanishEngine(LanguageEngine):
    code = "es"
    supported_modes = ("consonant", "assonant", "multisyllabic")
    default_mode = "consonant"
    function_words = SPANISH_FUNCTION_WORDS
    multisyllabic_supported = True
    key_specs = (
        KeySpec(name="consonant", fn=consonant_rhyme_key),
        KeySpec(name="assonant", fn=assonant_rhyme_key),
        KeySpec(name="multisyllabic", fn=multisyllabic_rhyme_key),
    )
    match_reasons = {
        "consonant": "shared ending from stressed vowel",
        "assonant": "shared vowel pattern from stressed vowel",
        "multisyllabic": "shared multisyllabic ending",
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
        return max(word_frequency(word, "es"), PR_SLANG.get(word, 0.0))

    def is_corpus_eligible_word(self, word: str) -> bool:
        if len(word) < 2:
            return False
        return bool(_SPANISH_WORD_RE.match(word))

    def is_same_stem_inflection(self, query: str, candidate: str) -> bool:
        return _es_is_same_stem_inflection(query, candidate)

    def inflection_forms(self, query: str) -> frozenset[str]:
        return _es_inflection_forms(query)

    def stress_signature(self, word: str) -> str | None:
        return _es_stress_signature(word)

    def candidate_tiers(
        self,
        index: "RhymeIndex",
        normalized: str,
        phonemes_list: list[tuple[str, ...]],
        mode: str,
        query_syllables: int,
    ) -> list[CandidateTier]:
        if mode == "multisyllabic":
            multi_keys = index.keys_for("multisyllabic", phonemes_list)
            multi_words = index.words_for(
                "multisyllabic", multi_keys, exclude=normalized
            )
            return [CandidateTier(name="multisyllabic", words=multi_words)]

        consonant_keys = index.keys_for("consonant", phonemes_list)
        assonant_keys = index.keys_for("assonant", phonemes_list)

        consonant_words = index.words_for(
            "consonant", consonant_keys, exclude=normalized
        )

        if mode == "assonant":
            # Pure assonant mode: return all vowel-pattern matches.
            # exclude=normalized already removes the query word itself.
            # We do NOT subtract the consonant set here — doing so would
            # hide words that are also perfect rhymes, and in assonant mode
            # the caller explicitly wants the broadest vowel-pattern pool.
            assonant_words = index.words_for(
                "assonant", assonant_keys, exclude=normalized
            )
            return [CandidateTier(name="assonant", words=assonant_words)]

        # mode == "consonant" — tiered cascade consonant → assonant.
        # Assonant tier is disjoint from consonant tier so the user doesn't
        # see the same word twice, which matches Spanish poetic convention.
        assonant_words = (
            index.words_for("assonant", assonant_keys, exclude=normalized)
            - consonant_words
        )
        return [
            CandidateTier(name="consonant", words=consonant_words),
            CandidateTier(name="assonant", words=assonant_words),
        ]
