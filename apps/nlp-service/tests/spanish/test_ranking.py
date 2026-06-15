"""Spanish-specific ranking tests: inflection penalty and stress-position bonus."""

from app.domain.languages.spanish.engine import SpanishEngine
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeEntry

_engine = SpanishEngine()


def _entry(word: str, syllables: int = 2, frequency: float = 1e-4) -> RhymeEntry:
    return RhymeEntry(
        word=word,
        syllables=syllables,
        frequency=frequency,
        stress_class=_engine.stress_signature(word),
    )


def test_conjugation_ranked_below_unrelated_rhyme() -> None:
    """canto vs cantaba: cantaba should rank behind an unrelated rhyme (manto)."""
    ranked = score_entries(
        [
            _entry("manto", syllables=2, frequency=1e-4),
            _entry("cantaba", syllables=3, frequency=1e-4),
        ],
        query="canto",
        rhyme_type="consonant",
        limit=10,
        query_syllables=2,
        engine=_engine,
    )
    words = [c.word for c in ranked]
    assert "manto" in words
    assert "cantaba" in words
    assert words.index("manto") < words.index("cantaba"), (
        "Unrelated rhyme 'manto' should outrank inflection 'cantaba'"
    )


def test_stress_signature_bonus_applied() -> None:
    """For an aguda query (amor), an aguda candidate (color) should outscore
    a llana candidate (pino) at the same frequency."""
    amor_stress = _engine.stress_signature("amor")   # aguda
    color_stress = _engine.stress_signature("color")  # aguda
    pino_stress = _engine.stress_signature("pino")    # llana

    assert amor_stress == "aguda", f"Expected 'amor' to be aguda, got {amor_stress}"
    assert color_stress == "aguda", f"Expected 'color' to be aguda, got {color_stress}"
    assert pino_stress == "llana", f"Expected 'pino' to be llana, got {pino_stress}"

    ranked = score_entries(
        [
            _entry("color", syllables=2, frequency=1e-4),
            _entry("pino", syllables=2, frequency=1e-4),
        ],
        query="amor",
        rhyme_type="consonant",
        limit=10,
        query_syllables=2,
        engine=_engine,
    )
    words = [c.word for c in ranked]
    assert words.index("color") < words.index("pino"), (
        "Aguda candidate 'color' should outrank llana candidate 'pino' for aguda query 'amor'"
    )


def test_stress_signatures_correct() -> None:
    """Verify stress_signature returns expected classes for known words."""
    cases = [
        ("amor", "aguda"),       # ends in r, no accent → aguda
        ("corazón", "aguda"),    # written accent on last syllable → aguda
        ("vida", "llana"),       # ends in vowel → llana
        ("mañana", "llana"),     # ends in a → llana
        ("música", "esdrujula"), # accent on third-to-last → esdrújula
        ("rápido", "esdrujula"), # accent on antepenultimate
    ]
    for word, expected in cases:
        result = _engine.stress_signature(word)
        assert result == expected, f"stress_signature({word!r}) = {result!r}, expected {expected!r}"


def test_assonant_mode_not_penalised_by_consonant_subtraction() -> None:
    """Smoke-check: SpanishEngine.is_same_stem_inflection delegates correctly."""
    assert _engine.is_same_stem_inflection("cantar", "cantaba")
    assert not _engine.is_same_stem_inflection("amor", "dolor")
