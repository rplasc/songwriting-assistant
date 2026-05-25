"""Heuristic tense classifier for lyric tokens.

English: small irregular map + suffix rules + auxiliary markers.
Spanish: paradigm-suffix matching against the verb-ending tables that
already exist for inflection detection. Both classifiers return None
when the token is not verb-like — silence is better than a wrong tense
in a consistency-drift check.

Spanish capability ships as ``partial`` because simplemma's
irregular-verb gaps (ser/ir/haber) mean some clear past/future tokens
will not be resolved. Returning None for those keeps confidence honest.
"""

from __future__ import annotations

from typing import Literal

Tense = Literal["past", "present", "future"]


# ── English ────────────────────────────────────────────────────────────────

_EN_PAST_IRREGULAR: frozenset[str] = frozenset(
    {
        "was", "were", "had", "did", "went", "saw", "took", "gave", "came",
        "ran", "felt", "knew", "made", "said", "told", "found", "thought",
        "left", "kept", "held", "got", "stood", "sat", "lost", "brought",
        "bought", "caught", "taught", "broke", "spoke", "wrote", "rode",
        "drove", "flew", "fell", "grew", "threw", "drew", "blew", "ate",
        "drank", "sang", "swam", "began", "rang", "shook", "woke", "wore",
    }
)
_EN_PRESENT_MARKERS: frozenset[str] = frozenset(
    {
        "am", "is", "are", "have", "has", "do", "does",
        "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
        "i've", "you've", "we've", "they've",
    }
)
_EN_FUTURE_MARKERS: frozenset[str] = frozenset(
    {
        "will", "shall", "won't", "shan't",
        "i'll", "you'll", "he'll", "she'll", "it'll", "we'll", "they'll",
    }
)
# Tokens we know are not verbs even though their suffix looks past-ish.
_EN_PAST_BLOCKLIST: frozenset[str] = frozenset(
    {
        "bed", "red", "fed", "wed", "led", "sled", "bread", "head", "dead",
        "good", "wood", "blood", "flood", "food",
    }
)


def _classify_english(token: str) -> Tense | None:
    if not token:
        return None
    if token in _EN_FUTURE_MARKERS:
        return "future"
    if token in _EN_PAST_IRREGULAR:
        return "past"
    if token in _EN_PRESENT_MARKERS:
        return "present"
    if token in _EN_PAST_BLOCKLIST:
        return None
    # Suffix rules — only when the surface form is plausibly a verb (>= 4 chars).
    if len(token) >= 4:
        if token.endswith("ed"):
            return "past"
        if token.endswith("ing"):
            return "present"
    return None


# ── Spanish ────────────────────────────────────────────────────────────────

# Order matters: longest endings first so "aremos" beats "as".
_ES_FUTURE_SUFFIXES: tuple[str, ...] = (
    "aremos", "eremos", "iremos",
    "aréis", "eréis", "iréis",
    "arán", "erán", "irán",
    "arás", "erás", "irás",
    "aré", "eré", "iré",
    "ará", "erá", "irá",
)
_ES_PAST_SUFFIXES: tuple[str, ...] = (
    # preterite
    "asteis", "isteis",
    "amos", "imos",
    "aron", "ieron",
    "aste", "iste",
    # imperfect
    "ábamos", "íamos",
    "abais", "íais",
    "aban", "ían",
    "abas", "ías",
    "aba", "ía",
    # singular preterite endings ending with stressed vowel
    "ó", "é", "í",
)
_ES_PRESENT_SUFFIXES: tuple[str, ...] = (
    # 1st/2nd person plural and 2nd person singular indicative
    "amos", "emos", "imos",
    "áis", "éis", "ís",
    "as", "es",
    "an", "en",
    "ando", "iendo",  # gerund — treat as present-progressive
)
# Common irregular present forms (estar/ser/ir/haber) — small whitelist so
# we don't lean entirely on simplemma.
_ES_PRESENT_IRREGULAR: frozenset[str] = frozenset(
    {
        "soy", "eres", "es", "somos", "sois", "son",
        "estoy", "estás", "está", "estamos", "estáis", "están",
        "voy", "vas", "va", "vamos", "vais", "van",
        "he", "has", "ha", "hemos", "habéis", "han", "hay",
        "tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen",
    }
)
_ES_PAST_IRREGULAR: frozenset[str] = frozenset(
    {
        "fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron",
        "era", "eras", "era", "éramos", "erais", "eran",
        "estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron",
        "tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron",
        "hizo", "hizo", "hicimos", "hicieron",
        "dije", "dijiste", "dijo", "dijimos", "dijeron",
    }
)


def _classify_spanish(token: str) -> Tense | None:
    if not token or len(token) < 3:
        return None
    if token in _ES_PRESENT_IRREGULAR:
        return "present"
    if token in _ES_PAST_IRREGULAR:
        return "past"
    for suf in _ES_FUTURE_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 2:
            return "future"
    for suf in _ES_PAST_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 2:
            return "past"
    for suf in _ES_PRESENT_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 2:
            return "present"
    return None


def classify_tense(token_normalized: str, language: str) -> Tense | None:
    if language == "en":
        return _classify_english(token_normalized)
    if language == "es":
        return _classify_spanish(token_normalized)
    return None


__all__ = ["Tense", "classify_tense"]
