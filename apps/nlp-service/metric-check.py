"""Quick dev tool for testing draft-level analysis without starting the server.

Usage:
    python metric-check.py draft.txt
    python metric-check.py draft.txt --language es
    python metric-check.py --stdin                        (pipe or paste)
    python metric-check.py --text "line one\nline two"

The draft file can include inline section labels like [verse] / [chorus] /
[bridge].  The tool prints section summaries, rhyme schemes, syllable
patterns, cadence classes, and draft-level insights.
"""

import argparse
import sys
import time


def _load(language: str):
    t0 = time.perf_counter()
    if language == "en":
        from app.domain.languages.english import EnglishEngine
        from app.repositories.cmudict_repository import CmuDictRepository

        repo = CmuDictRepository()
        engine = EnglishEngine()
    elif language == "es":
        from app.domain.languages.spanish import SpanishEngine
        from app.repositories.spanish_corpus import SpanishCorpus

        repo = SpanishCorpus()
        engine = SpanishEngine()
    else:
        raise SystemExit(f"unknown language: {language!r}")

    from app.services.language_router import LanguageContext
    from app.services.pronunciation_service import PronunciationService
    from app.services.rhyme_index import RhymeIndex
    from app.services.rhyme_service import RhymeService
    from app.services.syllable_service import SyllableService

    index = RhymeIndex(repo, engine)
    pron = PronunciationService(repo, engine)
    syl = SyllableService(repo, engine)
    rhymes = RhymeService(repo, index, pron, syl, engine)
    ctx = LanguageContext(
        engine=engine,
        repository=repo,
        index=index,
        pronunciation_service=pron,
        syllable_service=syl,
        rhyme_service=rhymes,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"[startup]  {language} loaded in {elapsed:.0f} ms  ({len(repo):,} words)\n")
    return ctx


def _analyze(content: str, language: str, ctx) -> None:
    from app.schemas.draft_analysis import DraftAnalysisRequest
    from app.services.draft_analysis_service import DraftAnalysisService

    request = DraftAnalysisRequest(language=language, content=content)
    service = DraftAnalysisService()

    t0 = time.perf_counter()
    result = service.analyze(request, ctx)
    elapsed = (time.perf_counter() - t0) * 1000

    print(f"[analysis]  {elapsed:.1f} ms  |  "
          f"{result.summary.section_count} section(s)  "
          f"{result.summary.line_count} lyric line(s)  "
          f"{result.summary.total_syllables} total syllables\n")

    if result.summary.notable_patterns:
        print("Notable patterns:")
        for p in result.summary.notable_patterns:
            print(f"  - {p}")
        print()

    for sec in result.sections:
        label_str = f" ({sec.label})" if sec.label else ""
        print("-" * 60)
        print(f"Section {sec.id}{label_str}  "
              f"lines {sec.line_start}-{sec.line_end}  "
              f"({sec.line_count} lyric line(s))")
        print(f"  Rhyme scheme   : {sec.rhyme_scheme or '-'}"
              f"  [{sec.rhyme_scheme_confidence}]")
        syl_str = "  ".join(str(n) for n in sec.syllable_pattern)
        print(f"  Syllables/line : {syl_str or '-'}")
        print(f"  Cadence        : {sec.cadence_class}  (stdev={sec.syllable_variance})")
    print("-" * 60)
    print()

    if result.insights:
        print("Insights:")
        for ins in result.insights:
            scope = f"[{ins.scope} > {ins.target}]" if ins.target else f"[{ins.scope}]"
            print(f"  [{ins.severity.upper():6}] {scope}  {ins.message}")
        print()

    print("Capabilities:")
    caps = result.capabilities
    for field, value in {
        "rhyme_scheme": caps.rhyme_scheme,
        "cadence_patterns": caps.cadence_patterns,
        "stress_hints": caps.stress_hints,
        "repetition": caps.repetition,
        "mixed_language": caps.mixed_language,
    }.items():
        print(f"  {field:<20} {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick draft-level metric checker")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("file", nargs="?", help="Path to a draft text file")
    group.add_argument("--stdin", action="store_true", help="Read draft from stdin")
    group.add_argument("--text", help="Inline draft text (use \\n for line breaks)")
    parser.add_argument("--language", default="en", choices=("en", "es"))
    args = parser.parse_args()

    if args.stdin:
        content = sys.stdin.read()
    elif args.text:
        content = args.text.replace("\\n", "\n")
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                content = fh.read()
        except OSError as e:
            raise SystemExit(f"could not read file: {e}") from e
    else:
        parser.print_help()
        raise SystemExit(1)

    content = content.strip()
    if not content:
        raise SystemExit("draft is empty")

    ctx = _load(args.language)
    _analyze(content, args.language, ctx)


if __name__ == "__main__":
    main()
