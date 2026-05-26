"""Phase 5.5 Milestone 3 evaluation report schemas.

The regression report exposes per-kind / per-language pass-rate and
latency statistics so the team can see at a glance whether the engine
still meets expectations after a change.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CONTRACT_VERSION = "phase-5.5.m3"

GoldenKind = Literal[
    "rhyme",
    "draft_semantic_repetition",
    "draft_motif_tracking",
    "draft_section_contrast",
    "draft_consistency_hints",
    "draft_compare",
]
Language = Literal["en", "es"]


class EvaluationReportRequest(BaseModel):
    kinds: list[str] | None = None
    languages: list[Language] | None = None
    include_cases: bool = False


class ReportTotals(BaseModel):
    cases: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0


class KindStats(BaseModel):
    cases: int = 0
    passed: int = 0
    failed: int = 0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    max_ms: float = 0.0


class CaseResult(BaseModel):
    kind: str
    language: Language
    name: str
    passed: bool
    failures: list[str] = []
    elapsed_ms: float


class EvaluationReportResponse(BaseModel):
    generated_at: str
    totals: ReportTotals
    by_kind: dict[str, KindStats]
    by_language: dict[str, KindStats]
    cases: list[CaseResult] | None = None
    contract_version: str = CONTRACT_VERSION
