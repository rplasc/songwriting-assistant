"""Shared loader for golden-set bundles.

Walks ``app/evaluation/golden_sets/**/cases.json``, filters by ``kind``
and ``language``, and yields typed ``LoadedCase`` records that both the
regression runner and the existing pytest suites consume. Centralizing
the loader keeps assertion logic and report generation in lockstep.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_GOLDEN_ROOT = Path(__file__).resolve().parent / "golden_sets"


@dataclass(frozen=True, slots=True)
class LoadedCase:
    kind: str
    language: str
    name: str
    bundle_path: Path
    payload: dict[str, Any]


def _iter_bundles(root: Path | None = None) -> Iterator[tuple[Path, dict[str, Any]]]:
    base = root or _GOLDEN_ROOT
    if not base.exists():
        return
    for path in base.rglob("cases.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        yield path, data


def _case_name(case: dict[str, Any]) -> str:
    if "name" in case and isinstance(case["name"], str):
        return case["name"]
    if "query" in case and isinstance(case["query"], str):
        return case["query"]
    return "(unnamed)"


def _case_language(case: dict[str, Any], bundle: dict[str, Any]) -> str:
    lang = case.get("language") or bundle.get("language")
    return str(lang) if lang else "en"


def load_cases(
    *,
    kinds: Iterable[str] | None = None,
    languages: Iterable[str] | None = None,
    root: Path | None = None,
) -> list[LoadedCase]:
    """Return all cases matching the given filters.

    ``kinds`` and ``languages`` are inclusive whitelists; ``None`` means
    "no filter". Bundles without a ``kind`` field default to ``"rhyme"``
    to match the historical convention of the first golden bundles.
    """
    kind_set = set(kinds) if kinds is not None else None
    lang_set = set(languages) if languages is not None else None
    out: list[LoadedCase] = []
    for path, bundle in _iter_bundles(root):
        bundle_kind = str(bundle.get("kind", "rhyme"))
        if kind_set is not None and bundle_kind not in kind_set:
            continue
        cases = bundle.get("cases", [])
        if not isinstance(cases, list):
            continue
        for case in cases:
            if not isinstance(case, dict):
                continue
            lang = _case_language(case, bundle)
            if lang_set is not None and lang not in lang_set:
                continue
            out.append(
                LoadedCase(
                    kind=bundle_kind,
                    language=lang,
                    name=_case_name(case),
                    bundle_path=path,
                    payload=case,
                )
            )
    return out


def all_known_kinds(root: Path | None = None) -> list[str]:
    seen: set[str] = set()
    for _, bundle in _iter_bundles(root):
        seen.add(str(bundle.get("kind", "rhyme")))
    return sorted(seen)


__all__ = ["LoadedCase", "all_known_kinds", "load_cases"]
