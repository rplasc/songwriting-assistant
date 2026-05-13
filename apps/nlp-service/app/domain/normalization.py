import re

_CONTRACTIONS: dict[str, str] = {
    "don't": "do not",
    "won't": "will not",
    "can't": "cannot",
    "i'm": "i am",
    "you're": "you are",
    "we're": "we are",
    "they're": "they are",
    "it's": "it is",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "i'll": "i will",
    "you'll": "you will",
    "he'll": "he will",
    "she'll": "she will",
    "we'll": "we will",
    "they'll": "they will",
    "i'd": "i would",
    "you'd": "you would",
    "he'd": "he would",
    "she'd": "she would",
    "we'd": "we would",
    "they'd": "they would",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "doesn't": "does not",
    "didn't": "did not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
}

_WORD_RE = re.compile(r"^[a-z][a-z'\-]*[a-z]?$")
_PUNCT_STRIP = "‘’“”\"'.,;:!?()[]{}<>"


def _flatten_quotes(text: str) -> str:
    return (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def normalize_word(text: str | None) -> str | None:
    """Lowercase, strip surrounding punctuation, collapse quotes.

    Returns None for empty input or anything that is not a recognizable word.
    """
    if not text:
        return None
    cleaned = _flatten_quotes(text).strip().strip(_PUNCT_STRIP).lower()
    if not cleaned:
        return None
    if not _WORD_RE.match(cleaned):
        return None
    return cleaned


def expand_basic_contractions(text: str) -> str:
    """Replace a small fixed map of contractions. Case-insensitive at the token level."""
    if not text:
        return text
    tokens = text.split()
    out: list[str] = []
    for tok in tokens:
        key = _flatten_quotes(tok).lower()
        stripped = key.strip(_PUNCT_STRIP)
        if stripped in _CONTRACTIONS:
            out.append(_CONTRACTIONS[stripped])
        else:
            out.append(tok)
    return " ".join(out)
