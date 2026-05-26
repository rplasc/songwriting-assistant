from app.domain.response_contracts.capability_reason_mapper import (
    base_capabilities,
    opt_in_capability,
    rhyme_capabilities,
)


def test_base_capabilities_defaults_opt_in_features_to_option_not_requested() -> None:
    caps = base_capabilities("en")
    assert caps.semantic_repetition.status == "unsupported"
    assert caps.semantic_repetition.reason_code == "option_not_requested"
    assert caps.motif_tracking.reason_code == "option_not_requested"
    assert caps.section_contrast.reason_code == "option_not_requested"
    assert caps.consistency_hints.reason_code == "option_not_requested"


def test_base_capabilities_marks_stress_hints_model_unavailable() -> None:
    caps = base_capabilities("en")
    assert caps.stress_hints.status == "unsupported"
    assert caps.stress_hints.reason_code == "model_unavailable"


def test_opt_in_capability_full_has_no_reason() -> None:
    cap = opt_in_capability("full")
    assert cap.status == "full"
    assert cap.reason_code is None


def test_opt_in_capability_partial_signals_language_partial_support() -> None:
    cap = opt_in_capability("partial")
    assert cap.status == "partial"
    assert cap.reason_code == "language_partial_support"


def test_rhyme_capabilities_marks_multisyllabic_unsupported_when_missing() -> None:
    caps = rhyme_capabilities(multisyllabic_supported=False)
    assert caps["multisyllabic"].status == "unsupported"
    assert caps["multisyllabic"].reason_code == "language_unsupported"
    assert caps["phrase_ending"].status == "full"
