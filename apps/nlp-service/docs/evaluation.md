# Evaluation and bench

This module ships an in-process regression runner and a compare-path
latency bench. Both share the same service code that backs the
`/v1/evaluation/regression-report` HTTP endpoint, so reports are
identical regardless of how you invoke them.

## Regression runner — CLI

```text
python -m app.evaluation.run_regression \
    [--kinds rhyme,draft_motif_tracking] \
    [--languages en,es] \
    [--json out.json] \
    [--markdown out.md] \
    [--include-cases]
```

- Walks every `app/evaluation/golden_sets/**/cases.json`.
- Dispatches each case to its kind-specific runner in
  [app/evaluation/case_runners.py](../app/evaluation/case_runners.py).
  Runners share assertion logic with the pytest suites so the CLI and
  `pytest` always agree.
- Exits `0` when every selected case passes, `1` otherwise. Suitable
  for ad-hoc CI inclusion.
- `--json` writes the full report; `--markdown` writes a human-friendly
  table with a failing-cases section.
- `--include-cases` controls whether the JSON output includes the
  per-case array (the markdown report always lists failures).

## Regression runner — HTTP endpoint

```text
POST /v1/evaluation/regression-report
{
  "kinds": ["rhyme", "draft_compare"],
  "languages": ["en"],
  "include_cases": false
}
```

The endpoint is gated by `settings.expose_evaluation_endpoint`
(`NLP_EXPOSE_EVALUATION_ENDPOINT` env var; default `True`). Set it to
`False` in environments where the route shouldn't be reachable. The
service returns `404` and the CLI keeps working.

### Report shape

```text
{
  "generated_at": "2026-05-25T17:45:27+00:00",
  "totals": { "cases": 42, "passed": 41, "failed": 1, "skipped": 0 },
  "by_kind":     { "rhyme": { p50_ms, p95_ms, max_ms, passed, failed, cases }, ... },
  "by_language": { "en":    { ... }, "es": { ... } },
  "cases":       [ ... ] | null,
  "contract_version": "phase-5.5.m3"
}
```

`CaseResult.failures` are short, human-readable assertion strings,
the same ones the pytest suites would print on failure.

## Compare-path latency bench

```text
python -m app.evaluation.bench_compare \
    [--iterations 30] \
    [--language en|es] \
    [--bundle short|medium|long]
```

- Calls `DraftCompareService.compare()` in-process, with no HTTP loopback.
- One warm-up call before timing starts.
- Prints `p50/p95/max/avg ms` plus a CSV-friendly row for piping into
  spreadsheets. No assertions; this tool is for measurement, not gating.

### Indicative budget

On a developer laptop the medium bundle should land in roughly **5–15 ms
p50**. Numbers vary across machines, so the bench prints them rather
than asserting them. Treat large deltas across runs as an investigation
signal, not a regression.

## Inducing a regression deliberately

To confirm the runner catches breakage:

1. Open one of the existing golden bundles, e.g.
   `app/evaluation/golden_sets/english/motif_tracking/cases.json`.
2. Replace an `expected_motifs` value with something the case can't
   produce (e.g., `["zzz"]`).
3. Re-run `python -m app.evaluation.run_regression --kinds draft_motif_tracking`.
4. The case should fail and the CLI should exit `1`. The same edit
   makes `pytest tests/test_phase5_draft_golden_sets.py` fail
   identically: both consumers share `case_runners.py`'s logic.

Revert the edit when done.

See also: [limitation-codes.md](./limitation-codes.md),
[confidence-and-evidence.md](./confidence-and-evidence.md).
