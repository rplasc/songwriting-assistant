from app.domain.nlp.phrase_clustering import PhraseRef, cluster_phrases


def _phrase(sid: str, line: int, text: str, lemmas: tuple[str, ...]) -> PhraseRef:
    return PhraseRef(section_id=sid, line_index=line, text=text, lemmas=lemmas)


def test_anchor_match_groups_listening_image() -> None:
    phrases = [
        _phrase("s1", 1, "I hear your shadow in the hall", ("hear", "shadow")),
        _phrase("s1", 2, "I hear your footsteps on the floor", ("hear", "footstep")),
    ]
    clusters = cluster_phrases(phrases)
    assert len(clusters) == 1
    assert clusters[0].members == phrases
    assert "hear" in clusters[0].signature


def test_high_jaccard_groups_full_overlap() -> None:
    phrases = [
        _phrase("s1", 1, "fire and ashes", ("fire", "ash")),
        _phrase("s1", 2, "fire and ashes", ("fire", "ash")),
    ]
    clusters = cluster_phrases(phrases)
    assert len(clusters) == 1


def test_no_overlap_creates_separate_clusters() -> None:
    phrases = [
        _phrase("s1", 1, "the sky is blue", ("sky", "blue")),
        _phrase("s1", 2, "the road is long", ("road", "long")),
    ]
    clusters = cluster_phrases(phrases)
    assert len(clusters) == 2


def test_single_lemma_phrases_only_cluster_when_lemma_matches() -> None:
    phrases = [
        _phrase("s1", 1, "fire", ("fire",)),
        _phrase("s1", 2, "fire", ("fire",)),
        _phrase("s2", 3, "rain", ("rain",)),
    ]
    clusters = cluster_phrases(phrases)
    signatures = sorted(c.signature for c in clusters)
    assert ("fire",) in signatures
    assert ("rain",) in signatures
    assert len(clusters) == 2


def test_empty_lemmas_skipped() -> None:
    phrases = [
        _phrase("s1", 1, "", tuple()),
        _phrase("s1", 2, "sky", ("sky",)),
    ]
    clusters = cluster_phrases(phrases)
    assert len(clusters) == 1
