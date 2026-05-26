from app.domain.response_contracts.revision_hash import (
    make_compare_analysis_id,
    make_revision_hash,
    options_signature,
)


def test_revision_hash_is_deterministic() -> None:
    a = make_revision_hash(language="en", content="line one\nline two")
    b = make_revision_hash(language="en", content="line one\nline two")
    assert a == b
    assert a.startswith("rev_")


def test_revision_hash_ignores_whitespace_noise() -> None:
    a = make_revision_hash(language="en", content="line one\nline two")
    b = make_revision_hash(language="en", content="   line one\nline two\n\n\n")
    assert a == b


def test_revision_hash_distinguishes_content() -> None:
    a = make_revision_hash(language="en", content="line one")
    b = make_revision_hash(language="en", content="line two")
    assert a != b


def test_revision_hash_distinguishes_options_signature() -> None:
    a = make_revision_hash(language="en", content="x", options_signature="motifs=1")
    b = make_revision_hash(language="en", content="x", options_signature="motifs=0")
    assert a != b


def test_compare_analysis_id_is_deterministic() -> None:
    sig = options_signature(
        compare_motifs=True,
        compare_repetition=True,
        compare_sections=True,
        compare_consistency=False,
    )
    a = make_compare_analysis_id(
        previous_hash="rev_aaa", current_hash="rev_bbb", options_signature=sig
    )
    b = make_compare_analysis_id(
        previous_hash="rev_aaa", current_hash="rev_bbb", options_signature=sig
    )
    assert a == b
    assert a.startswith("cmp_")


def test_compare_analysis_id_swap_changes_id() -> None:
    sig = options_signature(
        compare_motifs=True,
        compare_repetition=True,
        compare_sections=True,
        compare_consistency=False,
    )
    a = make_compare_analysis_id(
        previous_hash="rev_aaa", current_hash="rev_bbb", options_signature=sig
    )
    b = make_compare_analysis_id(
        previous_hash="rev_bbb", current_hash="rev_aaa", options_signature=sig
    )
    assert a != b
