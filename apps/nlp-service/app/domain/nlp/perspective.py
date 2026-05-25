"""Map pronouns (and Spanish possessive determiners) to grammatical person.

The lists are derived from the language-specific function_words modules
so the closed-class set stays canonical there. Person classification is
used by consistency_rules to flag perspective drift.
"""

from __future__ import annotations

from typing import Literal

Person = Literal["first", "second", "third"]


# English: subject/object/possessive/reflexive forms.
_ENGLISH_FIRST: frozenset[str] = frozenset(
    {
        "i", "me", "my", "mine", "myself",
        "we", "us", "our", "ours", "ourselves",
        "i'm", "i've", "i'll", "i'd", "we're", "we've", "we'll", "we'd",
    }
)
_ENGLISH_SECOND: frozenset[str] = frozenset(
    {
        "you", "your", "yours", "yourself", "yourselves",
        "you're", "you've", "you'll", "you'd",
    }
)
_ENGLISH_THIRD: frozenset[str] = frozenset(
    {
        "he", "him", "his", "himself",
        "she", "her", "hers", "herself",
        "it", "its", "itself",
        "they", "them", "their", "theirs", "themselves",
        "he's", "he'll", "he'd",
        "she's", "she'll", "she'd",
        "it's", "it'll",
        "they're", "they've", "they'll", "they'd",
    }
)


# Spanish: subject + object pronouns + possessive determiners that encode person.
# Note "tu" (your, sing.) and "su" (his/her/their) overlap with article forms in
# some readings, but in lyric context they almost always carry person — we keep
# them. "lo/la/los/las" overlap with articles and are *not* assigned a person
# here (too ambiguous to be reliable evidence).
_SPANISH_FIRST: frozenset[str] = frozenset(
    {
        "yo", "me", "mi", "mis", "mío", "mía", "míos", "mías",
        "nosotros", "nosotras", "nos", "nuestro", "nuestra",
        "nuestros", "nuestras",
    }
)
_SPANISH_SECOND: frozenset[str] = frozenset(
    {
        "tú", "tu", "tus", "te", "ti", "tuyo", "tuya", "tuyos", "tuyas",
        "vosotros", "vosotras", "os",
        "vuestro", "vuestra", "vuestros", "vuestras",
        "usted", "ustedes",  # second person by use even if grammatically third
    }
)
_SPANISH_THIRD: frozenset[str] = frozenset(
    {
        "él", "ella", "ellos", "ellas",
        "su", "sus", "suyo", "suya", "suyos", "suyas",
        "le", "les", "se",
    }
)


_PERSON_SETS: dict[str, tuple[frozenset[str], frozenset[str], frozenset[str]]] = {
    "en": (_ENGLISH_FIRST, _ENGLISH_SECOND, _ENGLISH_THIRD),
    "es": (_SPANISH_FIRST, _SPANISH_SECOND, _SPANISH_THIRD),
}


def classify_person(token_normalized: str, language: str) -> Person | None:
    if not token_normalized:
        return None
    sets = _PERSON_SETS.get(language)
    if sets is None:
        return None
    first, second, third = sets
    if token_normalized in first:
        return "first"
    if token_normalized in second:
        return "second"
    if token_normalized in third:
        return "third"
    return None


__all__ = ["Person", "classify_person"]
