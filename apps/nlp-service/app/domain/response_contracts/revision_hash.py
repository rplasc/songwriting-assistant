"""Deterministic revision and compare-analysis identifiers.

A revision hash anchors one side of a compare request. The same draft
content (after whitespace normalization) yields the same hash. The
compare analysis_id is a function of both sides' revision hashes plus
the compare options so an identical compare request reproduces the
same id end-to-end.
"""

from __future__ import annotations

import hashlib
import re


_BLANK_RUN = re.compile(r"\n{2,}")


def _normalize_content(content: str) -> str:
    # Strip leading/trailing whitespace and collapse runs of blank lines so
    # whitespace-only edits don't shift the hash. Internal single-line
    # breaks are preserved because they carry structural meaning.
    normalized = content.strip()
    normalized = _BLANK_RUN.sub("\n\n", normalized)
    return normalized


def make_revision_hash(
    *,
    language: str,
    content: str,
    options_signature: str = "",
) -> str:
    raw = f"{language}|{_normalize_content(content)}|{options_signature}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"rev_{digest}"


def make_compare_analysis_id(
    *,
    previous_hash: str,
    current_hash: str,
    options_signature: str,
) -> str:
    raw = f"{previous_hash}|{current_hash}|{options_signature}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"cmp_{digest}"


def options_signature(
    *,
    compare_motifs: bool,
    compare_repetition: bool,
    compare_sections: bool,
    compare_consistency: bool,
) -> str:
    return (
        f"motifs={int(compare_motifs)}|rep={int(compare_repetition)}|"
        f"sec={int(compare_sections)}|cons={int(compare_consistency)}"
    )


__all__ = [
    "make_compare_analysis_id",
    "make_revision_hash",
    "options_signature",
]
