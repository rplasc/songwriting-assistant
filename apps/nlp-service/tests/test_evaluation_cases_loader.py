from app.evaluation.cases_loader import all_known_kinds, load_cases


def test_load_cases_unfiltered_returns_all_bundles() -> None:
    cases = load_cases()
    assert cases, "expected at least one golden case to load"
    kinds = {c.kind for c in cases}
    # Sanity: the regression runner should see every M0-M3 family.
    assert "rhyme" in kinds
    assert "draft_motif_tracking" in kinds
    assert "draft_compare" in kinds


def test_load_cases_filters_by_kind() -> None:
    rhyme = load_cases(kinds=["rhyme"])
    assert rhyme, "expected rhyme cases"
    assert all(c.kind == "rhyme" for c in rhyme)


def test_load_cases_filters_by_language() -> None:
    en_only = load_cases(languages=["en"])
    assert en_only
    assert all(c.language == "en" for c in en_only)


def test_load_cases_kind_and_language_compose() -> None:
    cases = load_cases(kinds=["draft_compare"], languages=["es"])
    assert cases, "expected at least one Spanish compare case"
    assert all(c.kind == "draft_compare" and c.language == "es" for c in cases)


def test_all_known_kinds_includes_compare() -> None:
    assert "draft_compare" in all_known_kinds()
