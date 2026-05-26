"""Phase 5.5 M3 compare-path latency bench.

Runs ``DraftCompareService.compare()`` in-process across N iterations
of a fixed revision pair and prints p50/p95/max ms. No assertions —
pure measurement. Use this on demand; the regression runner is the
correctness check, this is the cost check.

Usage:

    python -m app.evaluation.bench_compare \\
        [--iterations 50] \\
        [--language en|es] \\
        [--bundle short|medium|long]
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time

from app.core.logging import configure_logging
from app.evaluation.run_regression import _build_router
from app.schemas.draft_compare import (
    DraftCompareOptions,
    DraftCompareRequest,
    DraftSide,
)
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.draft_compare_service import DraftCompareService
from app.services.draft_nlp_service import DraftNlpService


_BUNDLES_EN: dict[str, tuple[str, str]] = {
    "short": (
        "[verse]\nThe fire on the hill is burning\nThe fire in my chest still calls",
        "[verse]\nThe rain across the road is falling\nThe rain on every window calls",
    ),
    "medium": (
        "[verse]\nThe fire on the hill is burning\nThe fire in my chest still calls\n\n"
        "[chorus]\nHold me in the midnight window\nHold me when the city glows\n\n"
        "[verse]\nThe road below the moon is winding\nThe wind across the field still calls\n\n"
        "[chorus]\nHold me in the midnight window\nHold me when the city glows",
        "[verse]\nThe rain across the road is falling\nThe rain on every window calls\n\n"
        "[chorus]\nHold me in the midnight window\nHold me when the city glows\n\n"
        "[verse]\nThe river under stars is turning\nThe night across the porch still calls\n\n"
        "[chorus]\nHold me in the midnight window\nHold me when the city glows",
    ),
    "long": (
        "\n\n".join(
            [
                "[verse]\nThe fire on the hill is burning\nThe fire in my chest still calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[verse]\nThe road below the moon is winding\nThe wind across the field still calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[bridge]\nWe walk along the river bend\nWe trade our shadows for the light",
                "[verse]\nThe river under stars is turning\nThe night across the porch still calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[outro]\nUntil the morning finds us here",
            ]
        ),
        "\n\n".join(
            [
                "[verse]\nThe rain across the road is falling\nThe rain on every window calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[verse]\nThe road below the moon is winding\nThe wind across the field still calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[bridge]\nWe walk along the river bend\nWe trade our shadows for the light",
                "[verse]\nThe river under stars is turning\nThe night across the porch still calls",
                "[chorus]\nHold me in the midnight window\nHold me when the city glows",
                "[outro]\nUntil the morning finds us here",
            ]
        ),
    ),
}

_BUNDLES_ES: dict[str, tuple[str, str]] = {
    "short": (
        "[verso]\nEl fuego en la colina arde\nEl fuego en mi pecho llama",
        "[verso]\nLa lluvia en la colina cae\nLa lluvia en mi pecho llama",
    ),
    "medium": (
        "[verso]\nEl fuego en la colina arde\nEl fuego en mi pecho llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar",
        "[verso]\nLa lluvia en la colina cae\nLa lluvia en mi pecho llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar",
    ),
    "long": (
        "[verso]\nEl fuego en la colina arde\nEl fuego en mi pecho llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar\n\n"
        "[verso]\nEl río bajo el cielo gira\nLa noche en la ventana llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar",
        "[verso]\nLa lluvia en la colina cae\nLa lluvia en mi pecho llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar\n\n"
        "[verso]\nEl río bajo el cielo gira\nLa noche en la ventana llama\n\n"
        "[coro]\nVen conmigo a caminar\nVen conmigo a respirar",
    ),
}


def _bundle(language: str, name: str) -> tuple[str, str]:
    table = _BUNDLES_EN if language == "en" else _BUNDLES_ES
    if name not in table:
        raise SystemExit(f"unknown bundle {name!r}; valid: {sorted(table)}")
    return table[name]


def _percentile(values: list[float], pct: float) -> float:
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * pct
    floor = int(k)
    ceil = min(floor + 1, len(sorted_vals) - 1)
    if floor == ceil:
        return sorted_vals[floor]
    frac = k - floor
    return sorted_vals[floor] + (sorted_vals[ceil] - sorted_vals[floor]) * frac


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Compare-path latency bench")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--language", default="en", choices=["en", "es"])
    parser.add_argument(
        "--bundle", default="medium", choices=["short", "medium", "long"]
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    router = _build_router()
    nlp_service = DraftNlpService()
    analysis_service = DraftAnalysisService(nlp_service=nlp_service)
    compare_service = DraftCompareService(analysis_service=analysis_service)

    prev_content, cur_content = _bundle(args.language, args.bundle)
    ctx = router.get(args.language)
    request = DraftCompareRequest(
        language=args.language,  # type: ignore[arg-type]
        title=None,
        previous=DraftSide(content=prev_content),
        current=DraftSide(content=cur_content),
        options=DraftCompareOptions(),
    )

    # One un-measured warm-up to populate caches.
    compare_service.compare(request, ctx)

    timings: list[float] = []
    total_started = time.perf_counter()
    for _ in range(args.iterations):
        started = time.perf_counter()
        compare_service.compare(request, ctx)
        timings.append((time.perf_counter() - started) * 1000.0)
    total_ms = (time.perf_counter() - total_started) * 1000.0

    avg = statistics.mean(timings)
    p50 = _percentile(timings, 0.5)
    p95 = _percentile(timings, 0.95)
    max_ms = max(timings)
    print(
        f"compare bench: lang={args.language} bundle={args.bundle} "
        f"iterations={args.iterations} "
        f"p50={p50:.2f}ms p95={p95:.2f}ms max={max_ms:.2f}ms "
        f"avg={avg:.2f}ms total={total_ms:.0f}ms"
    )
    # CSV-friendly row for piping into spreadsheets.
    print(
        f"csv,{args.language},{args.bundle},{args.iterations},"
        f"{p50:.3f},{p95:.3f},{max_ms:.3f},{avg:.3f},{total_ms:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
