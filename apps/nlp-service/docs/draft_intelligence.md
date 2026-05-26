# Semantic Draft Intelligence

This document is the editorial source of truth for the design decisions. Consult it before changing thresholds,
capability labels, insight types, or the function-word filter.

For the API-level view, see [`draft-analysis.md`](./draft-analysis.md).
For the bilingual capability contract, see [`bilingual.md`](./bilingual.md).

**See also:**

- [`limitation-codes.md`](./limitation-codes.md) — closed set of `CapabilityReasonCode` values and what each signals.
- [`confidence-and-evidence.md`](./confidence-and-evidence.md) — how to interpret `Insight.confidence`, typed `evidence`, anchors, and rhyme-candidate `confidence` / `evidence_tags`.
- [`evaluation.md`](./evaluation.md) — running the regression runner and the compare-path latency bench.

---

## 1. New insight types

Five new values for `Insight.type` have been introduced:

| Type | Emitted by | When |
| --- | --- | --- |
| `semantic_repetition` | `semantic_repetition_rules.py` | Phrase cluster ≥ 2 members |
| `motif_concentration` | `motif_tracker.py` | A motif appears ≥ 3 times in one section |
| `section_contrast` | `section_contrast_rules.py` | Two sections are over-similar or under-varied |
| `perspective_drift` | `consistency_rules.py` | Dominant pronoun person flips between consecutive sections |
| `tense_drift` | `consistency_rules.py` | Dominant tense flips between consecutive sections |

Existing types (`repetition_ending`, `word_overuse`, `anaphora`) are unchanged.
Hook demotion can affect all five of the above plus `repetition_ending` and `word_overuse`.

---

## 2. New capability fields

`DraftAnalysisResponse.capabilities` gains four fields. All default to
`"unsupported"` when the corresponding option flag is `false`:

| Field | Option flag | Default |
| --- | --- | --- |
| `semantic_repetition` | `include_semantic_repetition` | `"unsupported"` |
| `motif_tracking` | `include_motif_tracking` | `"unsupported"` |
| `section_contrast` | `include_section_contrast` | `"unsupported"` |
| `consistency_hints` | `include_consistency_hints` | `"unsupported"` |

`DraftSummary.motifs` is populated when `include_motif_tracking` is `true`; it is an
empty list otherwise.

---

## 3. Content-lemma filtering

The shared helper `content_lemmas()` in
[`app/domain/nlp/content.py`](../app/domain/nlp/content.py) is the single entry point
for stripping function words before lemmatization. It is used by:

- `DraftNlpService` (section-bag construction for contrast detection)
- `phrase_clustering.py` (per-line phrase lemmas)
- `motif_rules.py` (draft-wide lemma locations)

The filter applies two rules in order:

1. Strip tokens whose normalized form is in the language's `FUNCTION_WORDS` set or
   whose length is < 2.
2. Lemmatize the remainder via `SimplemmaLemmatizer`.
3. Strip any lemma that ended up in `FUNCTION_WORDS` after lemmatization (e.g.,
   contractions that expand to a function word).

This ensures the function-word lists remain the canonical filter for both the phrase-
ending (M1) and semantic (M3/M4) code paths.

---

## 4. Simplemma coverage and known gaps

`simplemma>=1.1,<2` is the lemmatizer for both English and Spanish. Known limitations:

| Word (EN) | simplemma output | Correct lemma | Impact |
| --- | --- | --- | --- |
| `ran` | `rin` | `run` | Won't cluster with "running" / "run" |
| `went` | `wend` | `go` | Won't cluster with "going" / "goes" |
| `saw` (past) | `saw` | `see` or `saw` | Ambiguous; tense classifier handles via irregular map |

For Spanish, `ser`, `ir`, `haber`, `estar`, `tener` paradigms are partially handled via
the irregular whitelist in `tense.py`, but simplemma lemma quality for these verbs
remains unreliable. This is why `consistency_hints` capability is `"partial"` for `es`.

No workaround is applied for the English irregular pasts listed above. The limitation is
documented in `tests/test_lemmatization.py` and accepted at this scope. A heavier
lemmatizer (spaCy, stanza) would fix it but adds a significant dependency. The bar for
adding it is a golden-set failure attributable to lemma quality.

---

## 5. Phrase-clustering thresholds

Defined in
[`app/domain/nlp/phrase_clustering.py`](../app/domain/nlp/phrase_clustering.py):

| Constant | Value | Meaning |
| --- | --- | --- |
| `_JACCARD_THRESHOLD` | `0.5` | Primary cluster membership threshold |
| `_ANCHOR_MAX_LEMMAS` | `4` | Max content lemmas for anchor-match relaxation |
| `_ANCHOR_MIN_JACCARD` | `0.15` | Min Jaccard for anchor-match relaxation |

The anchor-match rule fires when **both** phrases have ≤ `_ANCHOR_MAX_LEMMAS` content
lemmas AND share their first content lemma AND Jaccard ≥ `_ANCHOR_MIN_JACCARD`. It was
set to 4 (not 2 or 3) because typical lyric lines carry 3–4 content words, and requiring
≤ 2 would exclude the common case entirely.

Do not raise `_ANCHOR_MIN_JACCARD` below 0.10 without running the golden sets — at very
low values, short phrases that share only one common word would cluster aggressively.

---

## 6. Motif thresholds

Defined in [`app/domain/nlp/motif_rules.py`](../app/domain/nlp/motif_rules.py):

| Constant | Value | Meaning |
| --- | --- | --- |
| `_MIN_LINES` | `3` | Minimum distinct lines a lemma must appear on |
| `_MIN_SECTIONS` | `2` | Minimum distinct sections a lemma must span (alternative to `_MIN_LINES`) |
| `_MAX_MOTIFS` | `6` | Maximum motifs returned per draft |
| `_MIN_LEMMA_LENGTH` | `3` | Minimum lemma character length to qualify |

Motifs are ranked by cross-section reach (descending) then total line frequency
(descending). The `_MIN_LEMMA_LENGTH = 3` filter is a secondary backstop against
residual short function words that escaped the function-word set filter.

---

## 7. Section contrast thresholds

Defined in
[`app/domain/draft_analysis/section_contrast_rules.py`](../app/domain/draft_analysis/section_contrast_rules.py):

| Constant | Value | Meaning |
| --- | --- | --- |
| `_OVER_SIMILARITY_THRESHOLD` | `0.85` | Jaccard ≥ this → `over_similarity` |
| `_LOW_VARIATION_THRESHOLD` | `0.15` | Jaccard ≤ this → `low_variation` (same-label only) |
| `_ENDING_OVERLAP_MIN` | `0.50` | Fraction of shared line endings for ending_overlap evidence |

Section labels compared: same-label pairs and verse↔chorus cross-label pairs.
Skipped labels: `bridge`, `outro`, `intro`, `pre-chorus`, `interlude`.

---

## 8. Consistency hint thresholds

Defined in
[`app/domain/draft_analysis/consistency_rules.py`](../app/domain/draft_analysis/consistency_rules.py):

| Constant | Value | Meaning |
| --- | --- | --- |
| `_DOMINANCE_RATIO` | `0.60` | Fraction of signals that must agree for a section to have a dominant value |
| `_MIN_SIGNALS` | `3` | Minimum person/tense signals required before making a determination |
| `_MIX_THRESHOLD` | `0.50` | No value above this AND ≥ 3 distinct values → internal-mix insight |

Drift insight is emitted when the dominant value in a section differs from the dominant
value in the immediately preceding section that also had a dominant. Sections below
`_MIN_SIGNALS` are transparent — they do not break a drift chain.

---

## 9. Hook demotion scope

[`app/domain/draft_analysis/hook_demotion.py`](../app/domain/draft_analysis/hook_demotion.py)
runs as the **final** step of every `POST /v1/analyze-draft` call, regardless of which
options are requested. This means previous insights (e.g., `repetition_ending` on a
chorus) are also demoted.

Hook labels that trigger demotion: `chorus`, `hook`, `refrain` (case-insensitive,
matching `ParsedSection.label` which is already lowercased by the section parser).

---

## 10. Golden sets and kind filter

Draft semantic golden sets live under
`app/evaluation/golden_sets/<language>/<feature>/cases.json` and carry a `"kind"` field:

| Kind | Test function | Feature |
| --- | --- | --- |
| `"rhyme"` | `test_phase5_golden_sets.py` | Rhyme suggestions (M1/M2) |
| `"draft_semantic_repetition"` | `test_phase5_draft_golden_sets.py` | Semantic repetition (M3) |
| `"draft_motif_tracking"` | `test_phase5_draft_golden_sets.py` | Motif tracking (M3) |
| `"draft_section_contrast"` | `test_phase5_draft_golden_sets.py` | Section contrast (M4) |
| `"draft_consistency_hints"` | `test_phase5_draft_golden_sets.py` | Consistency hints (M4) |

The rhyme golden-set runner (`test_phase5_golden_sets.py`) skips any bundle whose `kind`
is not `"rhyme"`. Without this filter, the rhyme test would post draft bundles to
`/v1/rhymes` and fail. Always include the `"kind"` field when authoring a new
`cases.json`.
