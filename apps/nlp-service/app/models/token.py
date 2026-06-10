from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Token:
    text: str
    normalized: str
    # Word-level position within its line. Populated by the tokenizers so that
    # downstream features (e.g. inner-rhyme highlighting) can map a token back
    # to a span the UI can highlight. Optional with None defaults so existing
    # callers that construct Token(text, normalized) keep working.
    index: int | None = None
    char_start: int | None = None
    char_end: int | None = None
