"""Phase 5.5 capability contract.

A ``Capability`` carries both a status and a machine-readable reason
code. The reason explains *why* a capability is partial or unsupported
so NestJS and Next.js can render consistent UI without re-deriving
language logic.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CapabilityStatus = Literal["full", "partial", "unsupported"]

# Closed enum of reason codes. ``None`` is used when status="full".
CapabilityReasonCode = Literal[
    "language_unsupported",
    "model_unavailable",
    "insufficient_lines",
    "option_not_requested",
    "language_partial_support",
]


class Capability(BaseModel):
    status: CapabilityStatus
    reason_code: CapabilityReasonCode | None = None


class Capabilities(BaseModel):
    rhyme_scheme: Capability
    cadence_patterns: Capability
    stress_hints: Capability
    repetition: Capability
    mixed_language: Capability
    semantic_repetition: Capability
    motif_tracking: Capability
    section_contrast: Capability
    consistency_hints: Capability


__all__ = [
    "Capability",
    "Capabilities",
    "CapabilityReasonCode",
    "CapabilityStatus",
]
