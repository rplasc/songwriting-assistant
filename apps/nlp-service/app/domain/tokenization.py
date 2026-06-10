from collections.abc import Iterator

from app.domain.normalization import normalize_word
from app.models.token import Token


def iter_word_spans(line: str) -> Iterator[tuple[str, int, int]]:
    """Yield ``(raw, char_start, char_end)`` for each whitespace-delimited token.

    Unlike ``str.split()`` this preserves each token's character offsets within
    the line, which inner-rhyme highlighting needs to point the UI at a word.
    ``char_end`` is exclusive (``line[char_start:char_end] == raw``).
    """
    if not line:
        return
    start: int | None = None
    for i, ch in enumerate(line):
        if ch.isspace():
            if start is not None:
                yield line[start:i], start, i
                start = None
        elif start is None:
            start = i
    if start is not None:
        yield line[start:], start, len(line)


def tokenize_line(line: str) -> list[Token]:
    """Split a line on whitespace, keeping each word's original text alongside its
    normalized form, word index, and character offsets. Pure-punctuation tokens
    are dropped; ``index`` reflects the order of kept words.
    """
    tokens: list[Token] = []
    for raw, char_start, char_end in iter_word_spans(line):
        norm = normalize_word(raw)
        if norm is None:
            continue
        tokens.append(
            Token(
                text=raw,
                normalized=norm,
                index=len(tokens),
                char_start=char_start,
                char_end=char_end,
            )
        )
    return tokens
