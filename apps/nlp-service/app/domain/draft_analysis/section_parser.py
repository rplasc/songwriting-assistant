"""Parse a draft into ordered sections with stable 1-based line indexes.

Source priority (matches the Phase 4 plan):
1. Explicit ``sections`` from the request — used verbatim; any blank or
   bracket-label lines inside the range are dropped from per-section
   ``lines`` but the original line indexes are preserved.
2. Inline ``[label]`` bracket lines — start a new section running until
   the next bracket or end of draft.
3. Blank-line stanza fallback — each non-empty run becomes one section.

The parser is intentionally deterministic. Returning ``[]`` is reserved
for content that contains no lyric lines at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_RECOGNIZED_LABELS: frozenset[str] = frozenset(
    {
        "verse",
        "chorus",
        "bridge",
        "outro",
        "intro",
        "pre-chorus",
        "prechorus",
        "hook",
        "refrain",
    }
)

_LABEL_LINE_RE = re.compile(r"^\s*\[\s*([A-Za-z][A-Za-z\- ]*?)\s*\]\s*$")


@dataclass(frozen=True, slots=True)
class ParsedLine:
    index: int  # 1-based line index in the original draft
    text: str


@dataclass(frozen=True, slots=True)
class ParsedSection:
    id: str
    label: str | None
    line_start: int
    line_end: int
    lines: tuple[ParsedLine, ...]


@dataclass(frozen=True, slots=True)
class _RawLine:
    index: int
    text: str
    is_blank: bool
    label: str | None  # set only when the line is an inline bracket label


def _parse_lines(content: str) -> list[_RawLine]:
    out: list[_RawLine] = []
    for i, raw in enumerate(content.split("\n"), start=1):
        stripped = raw.strip()
        if not stripped:
            out.append(_RawLine(i, raw, True, None))
            continue
        m = _LABEL_LINE_RE.match(raw)
        if m:
            label = _normalize_label(m.group(1))
            if label is not None:
                out.append(_RawLine(i, raw, False, label))
                continue
        out.append(_RawLine(i, raw, False, None))
    return out


def _normalize_label(raw: str) -> str | None:
    s = raw.strip().lower().replace(" ", "-")
    if s in _RECOGNIZED_LABELS:
        # Canonicalize: "prechorus" → "pre-chorus".
        if s == "prechorus":
            return "pre-chorus"
        return s
    return None


def parse_sections(
    content: str,
    explicit: list[tuple[str, str | None, int, int]] | None = None,
) -> list[ParsedSection]:
    """Resolve sections from ``content`` and optional explicit ranges.

    ``explicit`` items are ``(id, label, line_start, line_end)``. When provided
    and non-empty, they win. Otherwise the parser falls back to inline labels
    or blank-line stanzas.
    """
    raw_lines = _parse_lines(content)
    if not raw_lines:
        return []

    if explicit:
        return _sections_from_explicit(raw_lines, explicit)

    inline = _sections_from_inline_labels(raw_lines)
    if inline:
        return inline

    return _sections_from_stanzas(raw_lines)


def _sections_from_explicit(
    raw_lines: list[_RawLine],
    explicit: list[tuple[str, str | None, int, int]],
) -> list[ParsedSection]:
    by_index = {rl.index: rl for rl in raw_lines}
    out: list[ParsedSection] = []
    for sec_id, label, start, end in explicit:
        if end < start:
            start, end = end, start
        lines: list[ParsedLine] = []
        for idx in range(start, end + 1):
            rl = by_index.get(idx)
            if rl is None or rl.is_blank or rl.label is not None:
                continue
            lines.append(ParsedLine(rl.index, rl.text.strip()))
        out.append(
            ParsedSection(
                id=sec_id,
                label=label,
                line_start=start,
                line_end=end,
                lines=tuple(lines),
            )
        )
    return out


def _sections_from_inline_labels(raw_lines: list[_RawLine]) -> list[ParsedSection]:
    label_positions = [rl for rl in raw_lines if rl.label is not None]
    if not label_positions:
        return []

    out: list[ParsedSection] = []
    # If content exists before the first label, treat it as an unlabeled section.
    first_label_at = label_positions[0].index
    pre_label = [rl for rl in raw_lines if rl.index < first_label_at and not rl.is_blank]
    counter = 1
    if pre_label:
        out.append(
            _make_section(
                f"sec_{counter}",
                None,
                pre_label[0].index,
                pre_label[-1].index,
                pre_label,
            )
        )
        counter += 1

    label_lines = [rl for rl in raw_lines if rl.label is not None]
    for i, label_line in enumerate(label_lines):
        start = label_line.index
        end = (
            label_lines[i + 1].index - 1
            if i + 1 < len(label_lines)
            else raw_lines[-1].index
        )
        body = [
            rl
            for rl in raw_lines
            if start < rl.index <= end and not rl.is_blank and rl.label is None
        ]
        if not body:
            # Empty section after a label — keep it so the client can still see
            # the label, just with no lyric lines.
            out.append(
                ParsedSection(
                    id=f"sec_{counter}",
                    label=label_line.label,
                    line_start=start,
                    line_end=end,
                    lines=(),
                )
            )
        else:
            out.append(
                _make_section(
                    f"sec_{counter}",
                    label_line.label,
                    start,
                    end,
                    body,
                )
            )
        counter += 1
    return out


def _sections_from_stanzas(raw_lines: list[_RawLine]) -> list[ParsedSection]:
    out: list[ParsedSection] = []
    counter = 1
    current: list[_RawLine] = []

    def flush() -> None:
        nonlocal counter, current
        if not current:
            return
        out.append(
            _make_section(
                f"sec_{counter}",
                None,
                current[0].index,
                current[-1].index,
                current,
            )
        )
        counter += 1
        current = []

    for rl in raw_lines:
        if rl.is_blank:
            flush()
        else:
            current.append(rl)
    flush()
    return out


def _make_section(
    sec_id: str,
    label: str | None,
    start: int,
    end: int,
    body: list[_RawLine],
) -> ParsedSection:
    lines = tuple(ParsedLine(rl.index, rl.text.strip()) for rl in body)
    return ParsedSection(
        id=sec_id,
        label=label,
        line_start=start,
        line_end=end,
        lines=lines,
    )


__all__ = ["ParsedLine", "ParsedSection", "parse_sections"]
