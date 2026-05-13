"""Quick dev tool for testing rhymes and syllable counts without starting the server.

Usage:
    python check.py fire
    python check.py fire --limit 20
    python check.py "I see the fire in your eyes"
    python check.py fire heart night dream love broken tonight  (batch)
"""

import argparse
import time


def _load() -> tuple:
    t0 = time.perf_counter()
    from app.repositories.cmudict_repository import CmuDictRepository
    from app.services.pronunciation_service import PronunciationService
    from app.services.rhyme_index import RhymeIndex
    from app.services.rhyme_service import RhymeService
    from app.services.syllable_service import SyllableService

    repo = CmuDictRepository()
    index = RhymeIndex(repo)
    pron = PronunciationService(repo)
    syl = SyllableService(repo)
    rhymes = RhymeService(repo, index, pron, syl)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"[startup]  dictionary loaded in {elapsed:.0f} ms  ({len(repo):,} words)\n")
    return rhymes, syl


def _check_word(word: str, limit: int, rhyme_service, syllable_service) -> None:
    from app.domain.normalization import normalize_word
    from app.domain.tokenization import tokenize_line

    t0 = time.perf_counter()
    normalized, found, rhymes = rhyme_service.find_rhymes(word, limit)
    elapsed = (time.perf_counter() - t0) * 1000

    syl_count, syl_found = syllable_service.count_word(normalized or word)
    indicator = "" if found else " (not in dictionary)"

    print(f"word: {word!r}  ->  normalized: {normalized!r}{indicator}")
    print(f"syllables: {syl_count}  |  rhyme lookup: {elapsed:.1f} ms  |  {len(rhymes)} result(s)")
    if rhymes:
        for r in rhymes:
            print(f"  {r.word:<20} {r.syllables} syl")
    else:
        print("  (no rhymes found)")
    print()


def _check_line(line: str, syllable_service) -> None:
    from app.domain.tokenization import tokenize_line

    t0 = time.perf_counter()
    tokens = tokenize_line(line)
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
    args = parser.parse_args()

    rhyme_service, syllable_service = _load()

    for item in args.inputs:
        words = item.split()
        if len(words) > 1:
            _check_line(item, syllable_service)
        else:
            _check_word(item, args.limit, rhyme_service, syllable_service)


if __name__ == "__main__":
    main()
