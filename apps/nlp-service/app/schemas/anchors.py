"""Phase 5.5 insight anchors.

An anchor connects an insight back to a concrete location in the draft
so the client can jump to (or highlight) the relevant lines/section
without re-running analysis.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

AnchorScope = Literal["draft", "section"]


class InsightAnchor(BaseModel):
    scope: AnchorScope
    section_id: str | None = None
    line_start: int | None = None
    line_end: int | None = None


__all__ = ["AnchorScope", "InsightAnchor"]
