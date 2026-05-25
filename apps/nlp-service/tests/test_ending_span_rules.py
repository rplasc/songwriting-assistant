"""Phrase-ending span extraction rules."""

from __future__ import annotations

import pytest

from app.domain.languages.english.function_words import ENGLISH_FUNCTION_WORDS
from app.domain.languages.spanish.function_words import SPANISH_FUNCTION_WORDS
from app.domain.rhyme.ending_span_rules import extract_ending_span
from app.models.token import Token


def _toks(*words: str) -> list[Token]:
    return [Token(text=w, normalized=w.lower()) for w in words]


def test_empty_tokens_returns_none() -> None:
    assert extract_ending_span([], ENGLISH_FUNCTION_WORDS) is None


def test_single_content_word_is_returned_intact() -> None:
    span = extract_ending_span(_toks("night"), ENGLISH_FUNCTION_WORDS)
    assert span is not None
    assert span.normalized == ("night",)


def test_strips_leading_function_words_from_window() -> None:
    # "in the night" -> the 3-token window starts with two function words;
    # both should be stripped, leaving "night".
    span = extract_ending_span(
        _toks("in", "the", "night"), ENGLISH_FUNCTION_WORDS
    )
    assert span is not None
    assert span.normalized == ("night",)


def test_keeps_trailing_function_word_after_content() -> None:
    # "hold me" — "me" is a function word but trails a content word, so it
    # stays in the span (we strip leading function words only).
    span = extract_ending_span(_toks("hold", "me"), ENGLISH_FUNCTION_WORDS)
    assert span is not None
    assert span.normalized == ("hold", "me")
    assert span.span_text == "hold me"


def test_only_last_three_tokens_considered() -> None:
    # The window is the trailing max_tokens=3 tokens; preceding tokens
    # never enter the span.
    span = extract_ending_span(
        _toks("walked", "down", "the", "long", "lonely", "road"),
        ENGLISH_FUNCTION_WORDS,
    )
    assert span is not None
    assert span.normalized == ("long", "lonely", "road")


def test_window_all_function_words_falls_back_to_last_token() -> None:
    # "in the" — both function words. The extractor falls back to the very
    # last token so the engine still has something to look up; the rhyme
    # service will reject it downstream if no pronunciation exists.
    span = extract_ending_span(_toks("in", "the"), ENGLISH_FUNCTION_WORDS)
    assert span is not None
    assert span.normalized == ("the",)


def test_span_text_preserves_original_casing() -> None:
    tokens = [Token(text="Night", normalized="night")]
    span = extract_ending_span(tokens, ENGLISH_FUNCTION_WORDS)
    assert span is not None
    assert span.span_text == "Night"


@pytest.mark.parametrize(
    "raw,expected",
    [
        # Articles trimmed.
        (("en", "la", "noche"), ("noche",)),
        # Two content words trail; both kept.
        (("ventana", "abierta"), ("ventana", "abierta")),
        # Preposition + article + noun -> noun only.
        (("por", "el", "camino"), ("camino",)),
        # Trailing pronoun kept after content.
        (("dime", "lo"), ("dime", "lo")),
    ],
)
def test_spanish_examples(
    raw: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    span = extract_ending_span(_toks(*raw), SPANISH_FUNCTION_WORDS)
    assert span is not None
    assert span.normalized == expected
