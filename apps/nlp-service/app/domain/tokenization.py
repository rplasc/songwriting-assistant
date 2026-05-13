from app.domain.normalization import normalize_word
from app.models.token import Token


def tokenize_line(line: str) -> list[Token]:
    """Split a line on whitespace, keeping each word's original text alongside its
    normalized form. Pure-punctuation tokens are dropped.
    """
    if not line:
        return []
    tokens: list[Token] = []
    for raw in line.split():
        norm = normalize_word(raw)
        if norm is None:
            continue
        tokens.append(Token(text=raw, normalized=norm))
    return tokens
