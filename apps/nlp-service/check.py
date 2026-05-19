"""Quick dev tool for testing rhymes and syllable counts without starting the server.

Usage:
    python check.py fire
    python check.py fire --limit 20
    python check.py "I see the fire in your eyes"
    python check.py corazón --language es
    python check.py fire heart night dream love broken tonight  (batch)
"""

import argparse
import time


def _load(language: str) -> tuple:
    t0 = time.perf_counter()
    from app.services.language_router import LanguageContext

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
        raise SystemExit(f"unknown language: {language}")

    from app.services.pronunciation_service import PronunciationService
    from app.services.rhyme_index import RhymeIndex
    from app.services.rhyme_service import RhymeService
    from app.services.syllable_service import SyllableService

    index = RhymeIndex(repo, engine)
    pron = PronunciationService(repo, engine)
    syl = SyllableService(repo, engine)
    rhymes = RhymeService(repo, index, pron, syl, engine)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"[startup]  {language} loaded in {elapsed:.0f} ms  ({len(repo):,} words)\n")
    return rhymes, syl


def _check_word(word: str, limit: int, rhyme_service, syllable_service) -> None:
    t0 = time.perf_counter()
    normalized, found, mode, rhymes = rhyme_service.find_rhymes(word, limit)
    elapsed = (time.perf_counter() - t0) * 1000

    syl_count, syl_found = syllable_service.count_word(normalized or word)
    indicator = "" if found else " (not in dictionary)"

    print(f"word: {word!r}  ->  normalized: {normalized!r}{indicator}  [mode={mode}]")
    print(f"syllables: {syl_count}  |  rhyme lookup: {elapsed:.1f} ms  |  {len(rhymes)} result(s)")
    if rhymes:
        for r in rhymes:
            print(f"  {r.word:<20} {r.syllables} syl  ({r.rhyme_type}, {r.score:.2f})")
    else:
        print("  (no rhymes found)")
    print()


def _check_line(line: str, syllable_service, engine) -> None:
    t0 = time.perf_counter()
    tokens = engine.tokenize_line(line)
    total, per_token = syllable_service.count_tokens(tokens)
    elapsed = (time.perf_counter() - t0) * 1000

    print(f"line: {line!r}")
    print(f"total syllables: {total}  |  {elapsed:.1f} ms")
    for tok, count, found in per_token:
        flag = "" if found else " (?)"
        print(f"  {tok.normalized:<20} {count} syl{flag}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick rhyme/syllable checker")
    parser.add_argument("inputs", nargs="+", help="Word(s) or a quoted lyric line")
    parser.add_argument("--limit", type=int, default=10, help="Max rhymes to show (default 10)")
    parser.add_argument("--language", default="en", choices=("en", "es"))
    args = parser.parse_args()

    rhyme_service, syllable_service = _load(args.language)
    engine = rhyme_service._engine  # type: ignore[attr-defined]

    for item in args.inputs:
        words = item.split()
        if len(words) > 1:
            _check_line(item, syllable_service, engine)
        else:
            _check_word(item, args.limit, rhyme_service, syllable_service)


if __name__ == "__main__":
    main()
