import re

_CONTRACTIONS: dict[str, str] = {
    # negatives
    "don't": "do not",
    "won't": "will not",
    "can't": "cannot",
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
    "mustn't": "must not",
    "shan't": "shall not",
    "needn't": "need not",
    "ain't": "is not",
    # be
    "i'm": "i am",
    "you're": "you are",
    "we're": "we are",
    "they're": "they are",
    "it's": "it is",
    "he's": "he is",
    "she's": "she is",
    "that's": "that is",
    "there's": "there is",
    "here's": "here is",
    "what's": "what is",
    "who's": "who is",
    "where's": "where is",
    "how's": "how is",
    "let's": "let us",
    # have
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "would've": "would have",
    "should've": "should have",
    "could've": "could have",
    "might've": "might have",
    "must've": "must have",
    # will
    "i'll": "i will",
    "you'll": "you will",
    "he'll": "he will",
    "she'll": "she will",
    "we'll": "we will",
    "they'll": "they will",
    "it'll": "it will",
    "that'll": "that will",
    # would / had
    "i'd": "i would",
    "you'd": "you would",
    "he'd": "he would",
    "she'd": "she would",
    "we'd": "we would",
    "they'd": "they would",
    # lyric-style informal
    "y'all": "you all",
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "kinda": "kind of",
    "sorta": "sort of",
    "lemme": "let me",
    "gimme": "give me",
    "'cause": "because",
    "cuz": "because",
    "'em": "them",
    "'til": "until",
    "til": "until",
}

_WORD_RE = re.compile(r"^[a-z][a-z'\-]*[a-z]?$")
# Curly quotes (‘’“”) are absent here intentionally:
# _flatten_quotes normalises them to ASCII equivalents before this strip runs.
_PUNCT_STRIP = "\"'.,;:!?()[]{}<>—–"


def _flatten_quotes(text: str) -> str:
    return (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def normalize_word(text: str | None) -> str | None:
    """Lowercase, strip surrounding punctuation, collapse curly quotes.

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
    """Replace known contractions with their expanded form, case-insensitive."""
    if not text:
        return text
    tokens = text.split()
    out: list[str] = []
    for tok in tokens:
        key = _flatten_quotes(tok).lower()
        stripped = key.strip(_PUNCT_STRIP)
        # Try the bare token first, then a leading-apostrophe variant so things
        # like "'cause" still match after outer-punctuation stripping.
        if stripped in _CONTRACTIONS:
            out.append(_CONTRACTIONS[stripped])
        elif ("'" + stripped) in _CONTRACTIONS:
            out.append(_CONTRACTIONS["'" + stripped])
        else:
            out.append(tok)
    return " ".join(out)
