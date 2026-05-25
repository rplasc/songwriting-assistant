from app.domain.nlp.motif_rules import LemmaLocation, extract_motifs

_FN = frozenset({"the", "a", "is", "and"})


def test_extracts_lemma_recurring_across_sections() -> None:
    locs = [
        LemmaLocation("s1", 1, "fire"),
        LemmaLocation("s1", 2, "fire"),
        LemmaLocation("s2", 5, "fire"),
        LemmaLocation("s2", 6, "rain"),
    ]
    motifs = extract_motifs(locs, _FN)
    assert "fire" in motifs
    assert "rain" not in motifs  # only 1 line/section


def test_extracts_lemma_recurring_across_many_lines() -> None:
    locs = [LemmaLocation("s1", i, "shadow") for i in range(1, 4)]
    motifs = extract_motifs(locs, _FN)
    assert "shadow" in motifs


def test_function_words_filtered() -> None:
    locs = [LemmaLocation("s1", i, "the") for i in range(1, 10)]
    motifs = extract_motifs(locs, _FN)
    assert "the" not in motifs


def test_short_lemmas_filtered() -> None:
    locs = [LemmaLocation("s1", i, "go") for i in range(1, 10)]
    motifs = extract_motifs(locs, _FN)
    # length < 3 is filtered out
    assert "go" not in motifs


def test_empty_returns_empty() -> None:
    assert extract_motifs([], _FN) == []
