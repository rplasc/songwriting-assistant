# Confidence and evidence

The current contract surfaces three signals that consumers (NestJS,
Next.js) should treat differently when rendering insights or rhymes:
`confidence`, `evidence`, and `evidence_tags`. This document defines
each.

## `Insight.confidence`

`Insight.confidence` is `"low" | "medium" | "high" | null` and reflects
the **rule's** trust in its own claim, not the user's likely interest.

- **high** — the rule has strong evidence (multiple corroborating
  signals, dominant counts, high overlap). Safe to render with
  authoritative language.
- **medium** — the rule fired on a meaningful pattern but the signal is
  not lopsided. Render as a suggestion ("you might consider…"), not a
  verdict.
- **low** — the rule barely cleared its threshold. Render with
  exploratory phrasing, or surface only on demand.
- **null** — the insight family doesn't track confidence (e.g.
  `syllable_variance` is a direct measurement, not a judgment).

Severity (`info | low | medium | high`) is a separate axis: it's about
**editorial weight** (how distracting the issue is) rather than rule
trust. A repetition-opening insight in a chorus has `severity="info"`
because intentional, but its `confidence` stays the same as outside a
chorus.

## `Insight.evidence` — typed discriminated union

`evidence` is a `TypedEvidence` value discriminated by `kind`. Every
variant lives in [app/schemas/evidence.py](../app/schemas/evidence.py).
Consumers should branch on `kind` and read the fields they need
directly — no string parsing of `message`.

Stable variants by family:

| Family                | `kind`                              | Notable fields                                                       |
| --------------------- | ----------------------------------- | -------------------------------------------------------------------- |
| Cadence               | `syllable_variance`                 | `variance`, `cadence_class`                                          |
| Repetition (in-draft) | `repetition_opening`                | `phrase`                                                             |
|                       | `repetition_ending`                 | `word`                                                               |
|                       | `word_overuse`                      | `word`, `line_count`                                                 |
| Semantic              | `semantic_repetition`               | `lemmas`, `phrases`                                                  |
| Motif                 | `motif_concentration`               | `motif`, `section_count`                                             |
| Section               | `section_contrast`                  | `section_pair`, `jaccard`, `shared_lemmas`, `contrast_kind`          |
| Consistency           | `perspective_drift` / `tense_drift` | `from_section`, `to_section`, `from_value`, `to_value`               |
| Compare               | `motif_added` / `motif_removed`     | `motif`, `occurrences` / `previous_occurrences`                      |
|                       | `motif_strengthened` / `_weakened`  | `motif`, `previous`, `current`                                       |
|                       | `repetition_signal_added/removed`   | `signal_type`, `value`, `section_id`                                 |
|                       | `section_rhyme_scheme_shift`        | `section_id`, `previous`, `current`                                  |
|                       | `section_cadence_shift`             | `section_id`, `previous`, `current`                                  |
|                       | `section_syllable_pattern_shift`    | `section_id`, `previous`, `current`, `delta`                         |
|                       | `consistency_drift_resolved/intro…` | `drift_type`, `section_id`                                           |

`evidence` may be `null` only for insight families that have nothing
useful to attach (none today). Treat `null` as "no extra data" rather
than as an error.

## `Insight.anchor`

`anchor: InsightAnchor | null` tells the UI where to jump. `scope` is
`"draft"` (top-level) or `"section"`. When `scope="section"`,
`section_id` is always populated and `line_start` / `line_end` mirror
the section's bounds so the UI can highlight the affected lines.

## `Insight.hook_context`

A boolean flag set by the hook-demotion pass. When `true`, the insight
fired inside a chorus/hook/refrain where repetition is presumed
intentional — render with softer copy or hide. The flag lives on the
insight itself, not in `evidence`.

## `RhymeCandidate.confidence` and `evidence_tags`

Rhyme candidates carry their own `confidence` (`"high" | "medium" |
"low"`) plus a closed `evidence_tags` list. Mapping:

| Tag                       | Meaning                                                                |
| ------------------------- | ---------------------------------------------------------------------- |
| `shared_stressed_ending`  | Candidate matches on the final stressed phoneme cluster (true rhyme).  |
| `shared_vowel_pattern`    | Vowel skeleton matches but consonants drift (assonance / near rhyme).  |
| `shared_consonant_tail`   | Final consonant tail matches but vowel pattern doesn't (consonance).   |
| `multisyllabic_key_match` | Match anchors on a multi-syllable key, not just the final syllable.    |
| `phrase_ending_match`     | The candidate was produced by a phrase-ending query, not a single word.|
| `heuristic_fallback`      | The query didn't hit the pronunciation dictionary; results came from the heuristic G2P. Treat as lower-trust. |

Confidence layers on top:

- **high** for `perfect` or `multisyllabic` matches.
- **medium** for family-tier matches (shared trailing syllable).
- **low** for near-rhyme, assonant-only, or heuristic-fallback matches.

UIs should let the user dial in the floor (e.g., "only show high
confidence" or "include exploratory matches") rather than hide
low-confidence rhymes entirely — exploratory hits are often the most
useful.

See also: [limitation-codes.md](./limitation-codes.md),
[draft_intelligence.md](./draft_intelligence.md).
