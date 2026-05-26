"""Map capability state + reason into ``Capability`` instances.

Phase 5.5 promotes capability values from bare literals into models
with an explicit ``reason_code`` so consumers can distinguish
"unsupported because option not requested" from "unsupported because
language has no model".
"""

from __future__ import annotations

from app.schemas.capability import Capabilities, Capability, CapabilityReasonCode


def make_capability(
    status: str, reason_code: CapabilityReasonCode | None = None
) -> Capability:
    return Capability(status=status, reason_code=reason_code)  # type: ignore[arg-type]


def base_capabilities(language: str) -> Capabilities:
    """Build the base capability set for a language before option overlays."""
    # rhyme_scheme, cadence_patterns, repetition are language-agnostic full.
    # stress_hints stays unsupported until a real stress feature lands.
    # mixed_language is unsupported across both languages today.
    # The four Phase 5 opt-in features default to unsupported with a
    # reason of option_not_requested; the service will overlay them when
    # the caller asks for them.
    return Capabilities(
        rhyme_scheme=make_capability("full"),
        cadence_patterns=make_capability("full"),
        stress_hints=make_capability("unsupported", "model_unavailable"),
        repetition=make_capability("full"),
        mixed_language=make_capability("unsupported", "model_unavailable"),
        semantic_repetition=make_capability("unsupported", "option_not_requested"),
        motif_tracking=make_capability("unsupported", "option_not_requested"),
        section_contrast=make_capability("unsupported", "option_not_requested"),
        consistency_hints=make_capability("unsupported", "option_not_requested"),
    )


def opt_in_capability(
    status: str, language_partial: bool = False
) -> Capability:
    """Capability for an opt-in feature the caller asked for."""
    if status == "full":
        return make_capability("full")
    if status == "partial":
        return make_capability("partial", "language_partial_support")
    if language_partial:
        return make_capability("unsupported", "language_unsupported")
    return make_capability("unsupported", "model_unavailable")


def compare_capabilities(
    *,
    compare_motifs: bool,
    compare_repetition: bool,
    compare_sections: bool,
    compare_consistency: bool,
) -> dict[str, Capability]:
    def _flag(on: bool) -> Capability:
        return (
            make_capability("full")
            if on
            else make_capability("unsupported", "option_not_requested")
        )

    return {
        "compare_motifs": _flag(compare_motifs),
        "compare_repetition": _flag(compare_repetition),
        "compare_sections": _flag(compare_sections),
        "compare_consistency": _flag(compare_consistency),
    }


def rhyme_capabilities(*, multisyllabic_supported: bool) -> dict[str, Capability]:
    """Capabilities block for the /v1/rhymes response."""
    multi = (
        make_capability("full")
        if multisyllabic_supported
        else make_capability("unsupported", "language_unsupported")
    )
    return {
        "multisyllabic": multi,
        "phrase_ending": make_capability("full"),
    }


__all__ = [
    "base_capabilities",
    "compare_capabilities",
    "make_capability",
    "opt_in_capability",
    "rhyme_capabilities",
]
