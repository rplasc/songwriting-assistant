"""CLI entrypoint for the Phase 5.5 M3 regression runner.

Builds the same services ``main.lifespan`` builds (without starting an
HTTP server), runs ``EvaluationReportService.generate()``, and emits a
JSON and/or markdown report. Exit code is 0 when all selected cases
pass, 1 otherwise.

Usage:

    python -m app.evaluation.run_regression \\
        [--kinds rhyme,draft_motif_tracking] \\
        [--languages en,es] \\
        [--json out.json] \\
        [--markdown out.md] \\
        [--include-cases]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.logging import configure_logging, get_logger
from app.domain.languages.english import EnglishEngine
from app.domain.languages.spanish import SpanishEngine
from app.repositories.cmudict_repository import CmuDictRepository
from app.repositories.spanish_corpus import SpanishCorpus
from app.schemas.evaluation import EvaluationReportResponse
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.draft_compare_service import DraftCompareService
from app.services.draft_nlp_service import DraftNlpService
from app.services.evaluation_report_service import EvaluationReportService
from app.services.language_router import LanguageContext, LanguageRouter
from app.services.pronunciation_service import PronunciationService
from app.services.rhyme_index import RhymeIndex, warm_frequency_cache
from app.services.rhyme_service import RhymeService
from app.services.syllable_service import SyllableService


def _build_router() -> LanguageRouter:
    warm_frequency_cache()
    en_repo = CmuDictRepository()
    en_engine = EnglishEngine()
    en_index = RhymeIndex(en_repo, en_engine)
    en_pron = PronunciationService(en_repo, en_engine)
    en_syl = SyllableService(en_repo, en_engine)
    en_ctx = LanguageContext(
        engine=en_engine,
        repository=en_repo,
        index=en_index,
        pronunciation_service=en_pron,
        syllable_service=en_syl,
        rhyme_service=RhymeService(en_repo, en_index, en_pron, en_syl, en_engine),
    )

    es_repo = SpanishCorpus()
    es_engine = SpanishEngine()
    es_index = RhymeIndex(es_repo, es_engine)
    es_pron = PronunciationService(es_repo, es_engine)
    es_syl = SyllableService(es_repo, es_engine)
    es_ctx = LanguageContext(
        engine=es_engine,
        repository=es_repo,
        index=es_index,
        pronunciation_service=es_pron,
        syllable_service=es_syl,
        rhyme_service=RhymeService(es_repo, es_index, es_pron, es_syl, es_engine),
    )

    return LanguageRouter({"en": en_ctx, "es": es_ctx})


def _build_service() -> EvaluationReportService:
    router = _build_router()
    nlp_service = DraftNlpService()
    analysis_service = DraftAnalysisService(nlp_service=nlp_service)
    compare_service = DraftCompareService(analysis_service=analysis_service)
    return EvaluationReportService(
        language_router=router,
        draft_analysis_service=analysis_service,
        draft_compare_service=compare_service,
    )


def _markdown(report: EvaluationReportResponse) -> str:
    lines: list[str] = []
    lines.append("# Phase 5.5 regression report")
    lines.append("")
    lines.append(f"- Generated: {report.generated_at}")
    lines.append(f"- Contract: {report.contract_version}")
    lines.append("")
    t = report.totals
    lines.append(
        f"**Totals:** {t.passed}/{t.cases} passed ({t.failed} failed, {t.skipped} skipped)"
    )
    lines.append("")
    lines.append("## By kind")
    lines.append("")
    lines.append("| Kind | Passed | Failed | p50 ms | p95 ms | max ms |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for kind, stats in sorted(report.by_kind.items()):
        lines.append(
            f"| {kind} | {stats.passed} | {stats.failed} | "
            f"{stats.p50_ms} | {stats.p95_ms} | {stats.max_ms} |"
        )
    lines.append("")
    lines.append("## By language")
    lines.append("")
    lines.append("| Language | Passed | Failed | p50 ms | p95 ms | max ms |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for lang, stats in sorted(report.by_language.items()):
        lines.append(
            f"| {lang} | {stats.passed} | {stats.failed} | "
            f"{stats.p50_ms} | {stats.p95_ms} | {stats.max_ms} |"
        )
    if report.cases is not None:
        lines.append("")
        lines.append("## Failing cases")
        lines.append("")
        any_fail = False
        for c in report.cases:
            if c.passed:
                continue
            any_fail = True
            lines.append(f"- **{c.kind}/{c.language}/{c.name}** ({c.elapsed_ms} ms)")
            for f in c.failures:
                lines.append(f"  - {f}")
        if not any_fail:
            lines.append("_None._")
    lines.append("")
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 5.5 regression runner")
    parser.add_argument("--kinds", default=None, help="Comma-separated kinds filter")
    parser.add_argument(
        "--languages", default=None, help="Comma-separated languages (en,es)"
    )
    parser.add_argument("--json", dest="json_path", default=None, help="JSON output path")
    parser.add_argument(
        "--markdown", dest="md_path", default=None, help="Markdown output path"
    )
    parser.add_argument(
        "--include-cases",
        action="store_true",
        help="Include per-case results in the report",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    logger = get_logger("nlp.evaluation.cli")
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    kinds = [k.strip() for k in args.kinds.split(",")] if args.kinds else None
    languages = (
        [lang.strip() for lang in args.languages.split(",")]
        if args.languages
        else None
    )

    logger.info(
        "regression.start",
        extra={"extras": {"kinds": kinds, "languages": languages}},
    )
    service = _build_service()
    # Always include cases internally so the markdown report can list
    # failures. The flag only controls whether they end up in JSON.
    report = service.generate(kinds=kinds, languages=languages, include_cases=True)

    if args.json_path:
        payload = report.model_dump()
        if not args.include_cases:
            payload["cases"] = None
        Path(args.json_path).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    if args.md_path:
        Path(args.md_path).write_text(_markdown(report), encoding="utf-8")

    # Console summary so the CLI is useful without flags.
    print(
        f"{report.totals.passed}/{report.totals.cases} passed "
        f"({report.totals.failed} failed)"
    )
    if report.totals.failed and report.cases:
        print("Failing cases:")
        for c in report.cases:
            if not c.passed:
                print(f"  - {c.kind}/{c.language}/{c.name}: {'; '.join(c.failures)}")

    return 0 if report.totals.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
