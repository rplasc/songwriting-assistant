# Capability limitation codes

Every `Capability` returned by the NLP service carries a `status`
(`full` | `partial` | `unsupported`) and an optional machine-readable
`reason_code`. When `status="full"` the `reason_code` is always `null`.
For partial or unsupported capabilities the reason is one of the
following closed enum values.

| `reason_code`              | Meaning                                                                                   | Where it fires                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `language_unsupported`     | The capability has no implementation in the requested language at all.                    | Rhyme `multisyllabic` capability when the language engine doesn't define multisyllabic support.                 |
| `language_partial_support` | The capability has a degraded implementation for the requested language.                  | Draft analysis `consistency_hints` in Spanish — simplemma misses several irregular tenses.                      |
| `model_unavailable`        | The capability depends on a model/component that isn't wired up (yet).                    | Draft analysis `stress_hints` and `mixed_language` capabilities — both are placeholders for future work.        |
| `option_not_requested`     | The capability is gated behind a request option that the caller did not enable.           | Every opt-in field on `DraftAnalysisOptions` and `DraftCompareOptions` when its flag is `false`.                |
| `insufficient_lines`       | The capability ran but didn't have enough input to produce a confident result.            | Reserved — not yet emitted by any rule, but consumers should treat it as "the rule ran and decided to abstain". |

`reason_code` is part of the contract. New reasons get added to the
`CapabilityReasonCode` literal in
[app/schemas/capability.py](../app/schemas/capability.py) when a new
shape of failure shows up. Removing or renaming an existing code is a
breaking change.

## Capability blocks by endpoint

- **`/v1/analyze-draft`** → `Capabilities` (the typed model)
  - Always-on: `rhyme_scheme`, `cadence_patterns`, `repetition`
  - Model-gated: `stress_hints`, `mixed_language`
  - Option-gated: `semantic_repetition`, `motif_tracking`, `section_contrast`, `consistency_hints`
- **`/v1/rhymes`** → `dict[str, Capability]` with keys `multisyllabic`, `phrase_ending`.
- **`/v1/analyze-draft-compare`** → `CompareCapabilities` with the four `compare_*` flags.

When a client renders a capability badge, the rule is simple: show
`status` to the user, log/diagnose with `reason_code`.

See also: [confidence-and-evidence.md](./confidence-and-evidence.md),
[draft_intelligence.md](./draft_intelligence.md).
