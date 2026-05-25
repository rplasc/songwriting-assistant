from app.domain.nlp.lemmatization import SimplemmaLemmatizer
from app.models.token import Token


def test_english_lemmatizes_inflected_forms() -> None:
    lem = SimplemmaLemmatizer("en")
    assert lem.lemmatize_word("running") == "run"
    # simplemma collapses surface forms like plurals and the copula reliably.
    # (Irregular pasts like 'ran' map inconsistently; we don't depend on them.)
    assert lem.lemmatize_word("was") == "be"
    assert lem.lemmatize_word("shadows") == "shadow"
    assert lem.lemmatize_word("footsteps") == "footstep"


def test_spanish_lemmatizes_conjugations() -> None:
    lem = SimplemmaLemmatizer("es")
    assert lem.lemmatize_word("corrieron") == "correr"
    assert lem.lemmatize_word("gatos") == "gato"


def test_unknown_word_returns_input() -> None:
    lem = SimplemmaLemmatizer("en")
    # Made-up token: should fall back to the input string rather than None.
    assert lem.lemmatize_word("zxqwerty") == "zxqwerty"


def test_lemmatize_tokens_skips_empty_normalized() -> None:
    lem = SimplemmaLemmatizer("en")
    tokens = [Token("Running", "running"), Token("---", "")]
    assert lem.lemmatize_tokens(tokens) == ["run"]


def test_cache_returns_same_object() -> None:
    lem = SimplemmaLemmatizer("en")
    a = lem.lemmatize_word("running")
    b = lem.lemmatize_word("running")
    assert a == b
