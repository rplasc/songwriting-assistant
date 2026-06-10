# Draft Analysis

Design decisions for `POST /v1/analyze-draft` and the `DraftAnalysisService`. For the
cross-language view, see [`bilingual.md`](./bilingual.md). For the broader service
tradeoffs, see [`service-overview.md`](./service-overview.md).

---

## What the endpoint does

`POST /v1/analyze-draft` accepts a full song draft (as raw text) plus an optional list
of explicitly labelled sections. It returns a `DraftAnalysisResponse` containing:

- **`capabilities`** — what this language currently supports at draft level.
- **`summary`** — total line count, syllable count, and notable patterns rolled up across all sections.
- **`sections`** — per-section breakdown: rhyme scheme, syllable pattern, cadence class, and repetition signals.
- **`insights`** — actionable observations with severity levels (`info`, `low`, `medium`, `high`).
- **`inner_rhymes`** — word-level rhyme groups (perfect/near) with line/word/char
  positions, for highlighting rhymes anywhere in the draft, not just line endings.
  See [`inner-rhyme-detection.md`](./inner-rhyme-detection.md).

---

## 1. Section parsing: explicit beats heuristic

**Decision:** If the request includes a `sections` array, the service maps each section
directly to the named line ranges in `content`. If sections are omitted, the service
falls back to heuristic parsing in
[`section_parser.py`](../app/domain/draft_analysis/section_parser.py), which splits
on blank lines and infers labels from header-like text ("Verse 1:", "Chorus", etc.).

**Reasoning:**

The web client already has a structured view of the draft: it knows which lines belong
to which section and has assigned labels. Sending that structure with the request costs
nothing and lets the service skip a fragile heuristic entirely.

The heuristic exists because not all callers will have structured section data. A plain
text submission (curl, future integrations) should still produce a useful response
rather than a validation error.

**Tradeoffs:**

- When the client provides sections, `line_start` / `line_end` must refer to
  1-indexed lines in `content`. Off-by-one errors in the client become silent
  wrong-section assignments rather than errors; the service trusts the caller's
  line ranges.
- The heuristic is opinionated about what counts as a section header. Drafts with
  unusual formatting may produce unexpected groupings. The `label` field in each
  `SectionAnalysis` reflects what the parser inferred; the client can display it to
  the user for verification.

---

## 2. Rhyme scheme assignment keys from the last word of each line

**Decision:** The rhyme key for each line is derived from the last token's pronunciation,
not from any word in the line. [`assign_scheme`](../app/domain/draft_analysis/rhyme_scheme_rules.py)
takes a list of keys (one per line) and returns a scheme string (`"ABAB"`, `"AABB"`, etc.)
plus a confidence level (`"full"` or `"partial"`).

**Reasoning:**

End rhyme is the dominant rhyme convention in popular songwriting. Internal rhyme,
alliteration, and near-rhyme patterns matter too, but they require prosody analysis
that is deferred. Deriving a single key per line keeps the scheme assignment problem
tractable: it is a straightforward equivalence-class labeling over a list of strings.

**Tradeoffs:**

- Lines whose last word has no known pronunciation (English unknown word with no
  heuristic tail, or a Spanish word that fails G2P) yield a `None` key. `assign_scheme`
  treats `None` as a wildcard: it does not create a rhyme class for it. This degrades
  gracefully: a scheme like `"A?BA"` becomes `"ABA"` with `"partial"` confidence.
- Identical end words always match each other, even if the repetition is coincidental.
  The repetition detection module catches these cases separately.

---

## 3. Per-request rhyme key cache

**Decision:** `DraftAnalysisService._line_rhyme_key` caches results in a plain
`dict[str, str | None]` keyed on `"<lang>:<word>"`. The cache lives for the duration
of one `analyze` call and is discarded after.

**Reasoning:**

A verse with 16 lines may end on the same handful of words many times (hook repetition,
rhyme scheme density). Recomputing pronunciation lookups and G2P for the same word on
every line wastes time. The per-request dict is the simplest structure that eliminates
that redundancy without introducing shared mutable state across requests.

**Tradeoffs:**

- The cache holds raw rhyme keys (`str | None`), not `Pronunciation` objects, so it
  cannot be reused for other lookups within the same request. A richer cache would
  allow reuse across the rhyme scheme and repetition modules, but that isn't worth it yet.
- The cache is not bounded. A pathological draft with 64 unique end words would hold
  64 entries. At current limits (64 sections × ~80 lines max) this is irrelevant.

---

## 4. Cadence classification from syllable variance

**Decision:** [`classify_pattern`](../app/domain/draft_analysis/cadence_rules.py)
takes the list of per-line syllable counts for a section and returns a `CadenceResult`
with a `cadence_class` (`"consistent"`, `"mixed"`, or `"varied"`), a variance float,
and a pre-formatted severity message for the insights list.

Section label is also passed so that chorus and hook sections can apply looser variance
thresholds, since structured repetition in a hook is not a problem.

**Reasoning:**

Syllable variance is a simple proxy for whether the section feels metrically coherent.
Consistent syllable counts signal that the songwriter is working with a rhythmic
framework; high variance signals that lines may not sit naturally on the same melody.

Routing the severity message through the classifier (rather than in the service) keeps
the classification logic and its human-readable output in the same module.

**Tradeoffs:**

- Variance is a blunt instrument. A pattern like `[8, 6, 8, 6]` (alternating) reads as
  "varied" by raw variance but may be completely intentional. A future improvement would
  detect alternating patterns explicitly and classify them as `"consistent"`.
- The thresholds (what variance counts as "mixed" vs. "varied") are hard-coded in
  `cadence_rules.py`. They were calibrated informally against example drafts. A tuning
  pass against a golden set would improve precision.

---

## 5. Two-level repetition detection: section signals and draft overuse

**Decision:** Repetition is detected in two passes:

1. **Section signals** — [`detect_section_signals`](../app/domain/draft_analysis/repetition_rules.py)
   looks for opening-phrase anaphora and repeated line-ending words within each section.
2. **Draft overuse** — [`detect_draft_overuse`](../app/domain/draft_analysis/repetition_rules.py)
   looks for words that appear on too many lines across the whole draft.

**Reasoning:**

The two patterns have different meaning and different scope. Anaphora ("I see... / I
feel... / I know...") is a stylistic device that is normal in a chorus but unusual in a
verse, and the section-level pass can account for the label. Word overuse ("love" on 10 of
16 lines) is a draft-level concern that only becomes visible when all sections are
combined.

Separating the passes keeps each rule focused and prevents cross-contamination: a word
that repeats intentionally within a chorus does not count toward its draft-level overuse
score.

**Tradeoffs:**

- Draft overuse uses a simple line-count threshold. The same word appearing once per
  line in a 4-line verse reads differently than once per line across a 20-line draft.
  Severity (`medium` / `high`) escalates at 5 lines regardless of total draft length.
  A proportional threshold would be more nuanced.
- Section signals are emitted for every matching pattern. If a section has both
  opening-phrase anaphora and repeated endings, both insights appear. This is intentional
  (both are worth surfacing), but it can produce a noisy insights list for highly
  structured drafts.

---

## 6. Capability manifest per language

**Decision:** `_BASE_CAPABILITIES` in `DraftAnalysisService` is a static dict keyed by
language code. Every response includes the resolved capabilities so the client knows
exactly what the analysis covers for the language requested.

**Reasoning:**

Not all features are implemented for all languages at the same time. Stress-hint
insights and mixed-language detection are deferred. Returning a `capabilities` object
lets the client grey out or annotate features that are not available, rather than the
client hardcoding what each language supports.

**Tradeoffs:**

- `_BASE_CAPABILITIES` is a plain dict in source code, not driven by the engine
  interface. Adding a language requires updating this dict by hand. The engine could
  expose a `draft_capabilities()` method to make this automatic; the current scale
  doesn't justify the indirection.
- Both `en` and `es` currently declare identical capabilities. The dict will diverge
  if stress hints are added for Spanish (which has deterministic stress) before English.

---

---

## 6. Opt-in semantic analysis via `DraftAnalysisOptions`

**Decision:** Lemma-backed features (semantic repetition detection and
motif tracking) were added behind two opt-in flags:

```json
{
  "language": "en",
  "content": "...",
  "options": {
    "include_semantic_repetition": true,
    "include_motif_tracking": true
  }
}
```

When neither flag is set, the response is identical to old versions. Capabilities
for these features read `"unsupported"` in the default case.

**Reasoning:**

Lemmatization via `simplemma` adds measurable latency for drafts with many unique
tokens. Clients that do not need the semantic layer (line-level keystroke calls,
lightweight mobile views) should not pay that cost. The opt-in flags make the
contract explicit and keep backward compatibility absolute: no existing test needed
to change.

**Tradeoffs:**

- Two flags rather than one means clients can request motif tracking without semantic
  repetition (or vice versa). In practice the two features share a single
  lemmatization pass inside `DraftNlpService.analyze`, so the latency difference
  between requesting one vs. both is negligible. The separate flags preserve
  fine-grained client control.
- `simplemma` handles most English and Spanish forms correctly but mis-lemmatizes
  some English irregular pasts (`ran → rin`, `went → wend`). This is documented in
  `tests/test_lemmatization.py` and is an accepted limitation at this scope;
  a more accurate lemmatizer would require a heavier dependency.

---

## 7. Phrase clustering via content-lemma Jaccard

**Decision:** [`phrase_clustering.py`](../app/domain/nlp/phrase_clustering.py) groups
lines into clusters when their content-lemma bags overlap sufficiently. The primary
threshold is Jaccard ≥ 0.5. A relaxed anchor-match rule fires when:

- both phrases have ≤ 4 content lemmas (common in short lyric lines), AND
- they share their first content lemma (the "anchor"), AND
- Jaccard ≥ 0.15 (at least partial structural overlap).

**Reasoning:**

Full Jaccard 0.5 is too strict for short lyric lines. "Hear your shadow in the hall"
and "Hear your footsteps on the floor" share only one content lemma ("hear") out of
three each, so raw Jaccard is 1/5 = 0.20. Without the anchor-match relaxation they
would not cluster, and the semantic repetition detector would miss a clear structural
parallel. The anchor rule captures the songwriter's intent: two lines that start on
the same idea are usually variants of the same phrase, even if the trailing imagery
differs.

**Tradeoffs:**

- The anchor rule increases false-positive clustering for short phrases that coincidentally
  share a common first content word (e.g., two lines starting with "feel"). The Jaccard
  ≥ 0.15 floor limits this: it still requires at least one additional shared lemma
  beyond the anchor for 3-lemma phrases.
- Content lemmas are derived by stripping function words then lemmatizing. The
  function-word filter reuses the lists from
  [`english/function_words.py`](../app/domain/languages/english/function_words.py)
  and [`spanish/function_words.py`](../app/domain/languages/spanish/function_words.py)
  rather than duplicating them, keeping the two word lists as the single source of truth.

---

## 8. Motif qualification thresholds

**Decision:** A content lemma qualifies as a motif when it appears on ≥ 3 distinct
lines **or** in ≥ 2 distinct sections. At most 6 motifs are returned per draft, ranked
by cross-section reach then raw frequency.

**Reasoning:**

A word that appears once per section in a verse + chorus structure (2 sections, 2 lines)
should be surfaced as a motif: it signals a recurring thematic anchor even if it only
appears twice. The cross-section criterion catches that case while the ≥ 3 lines
criterion catches within-section repetition. The 6-motif cap prevents the motifs list
from being swamped by generic words that survived the function-word filter.

**Tradeoffs:**

- The thresholds (3 lines, 2 sections, max 6) are calibrated from inspection of small
  drafts (16–24 lines). Longer drafts with many sections may need proportional thresholds.
  This is a known simplification.
- Function words with length < 3 are additionally filtered (`min_length=3`). This catches
  residual connectives ("so", "to", "by") that are not in the function-word set.

---

## 9. Semantic repetition confidence gating

**Decision:** `detect_semantic_repetition` assigns confidence based on cluster scope:

| Condition | Confidence | Severity |
| --- | --- | --- |
| ≥ 3 lines in the same section | `high` | `medium` |
| 2 lines in the same section | `medium` | `low` |
| Lines in different sections | `low` | `low` |

**Reasoning:**

Cross-section repetition is sometimes intentional (a motif or refrain) and sometimes
accidental. Surfacing it at `low` confidence signals "this is a pattern worth noticing"
without asserting it is a problem. Within-section repetition with three or more
occurrences is a stronger signal that the songwriter may be cycling on the same phrase
unintentionally.

**Tradeoffs:**

- `low` confidence cross-section insights may produce noisy results for structured
  song forms where the same imagery repeats across bridge and verse intentionally.
  The hook demotion pass (see §12) further softens these for chorus/hook sections.

---

## 10. Section contrast detection

**Decision:** [`section_contrast_rules.py`](../app/domain/draft_analysis/section_contrast_rules.py)
compares section pairs using Jaccard over content-lemma bags:

- **Same-label pairs** (verse↔verse, chorus↔chorus): Jaccard ≥ 0.85 → `over_similarity`
  (severity `medium`); Jaccard ≤ 0.15 → `low_variation` (severity `low`).
- **Verse↔chorus pairs**: only the `over_similarity` end is checked. A verse that
  is nearly identical to a chorus suggests the chorus is doing double duty.
- **Bridge, outro, intro**: skipped. These sections typically have unique structural
  roles and comparison against other types would produce mostly noise.

A secondary signal attaches `ending_overlap: true` to the evidence when ≥ 50% of
line-ending words are shared between the pair.

**Reasoning:**

Same-label sections are the natural comparison unit for revision: a songwriter revising
verse 2 needs to know whether it adds anything new compared to verse 1. Verse↔chorus
comparison catches the specific failure mode where the verse and chorus are
interchangeable, which eliminates the structural contrast that distinguishes the sections.

**Tradeoffs:**

- Jaccard 0.85 is a high bar; two sections must share nearly all their content lemmas
  before flagging. This avoids false positives on sections that share thematic vocabulary
  (both about loss, both about love) but are lyrically distinct. Reducing the threshold
  would surface more pairs but increase noise.
- O(s²) pair comparison where s is section count, capped at 64 sections per request.
  At that cap, 64×63/2 = 2016 pair comparisons, which is negligible.

---

## 11. Consistency hints (perspective and tense drift)

**Decision:** Two detectors run over per-section token classifications:

- **Perspective drift** — `detect_perspective_drift` classifies each token as first,
  second, or third person using pronoun sets drawn from the function-word lists.
  A section whose dominant person (≥ 60% of person-bearing tokens) differs from
  the previous section's dominant person generates a `perspective_drift` insight.
  An internally mixed section (no value above 50%, ≥ 4 person tokens, ≥ 3 distinct
  values) also generates an insight.
- **Tense drift** — `detect_tense_drift` classifies tokens as past/present/future using
  suffix heuristics and auxiliary-marker tables. Same dominance rules apply.

Both detectors require at least 3 person/tense signals in a section before making a
determination (`_MIN_SIGNALS = 3`). Sections with fewer signals produce no insight.

**Reasoning:**

Songs that inadvertently flip from "I" to "you" mid-draft or that mix past tense
storytelling with present-tense chorus feel disorienting to listeners. Both are
concrete, detectable patterns with a high signal-to-noise ratio when the evidence
threshold is met.

Requiring 3+ signals before committing to a dominant category prevents false positives
on sections with very few pronouns/verbs (a two-line bridge mentioning "you" once does
not constitute second-person commitment).

**Tradeoffs:**

- Intentional perspective shifts (a song that talks to a lost loved one in the chorus but
  narrates in third person in the verse) will produce false-positive drift insights.
  Severity is deliberately set to `low` so the hint is advisory.
- Spanish tense detection is marked `partial` because `simplemma` mis-lemmatizes common
  irregular verbs (ser, ir, haber, estar). The tense classifier includes irregular
  whitelists for these but coverage is incomplete. The `partial` capability label is
  the honest exposure of that limitation.
- EN tense drift confidence is `medium`; ES is `low` to reflect the additional uncertainty.

---

## 12. Hook demotion

**Decision:** After all insights are assembled, a final pass
[`demote_inside_hooks`](../app/domain/draft_analysis/hook_demotion.py) downgrades
severity for insights targeting chorus, hook, or refrain sections:

| Original severity | After demotion |
| --- | --- |
| `high` | `medium` |
| `medium` | `low` |
| `low` | `info` |

Only the types `semantic_repetition`, `repetition_ending`, and `word_overuse` are
demotable. For draft-scoped `word_overuse`, demotion applies only when every occurrence
of the overused word is inside hook sections. Evidence gains `"hook_context": true`.

**Reasoning:**

Repetition in a chorus is structurally intentional: the hook _should_ repeat its
central phrase and end-rhyme pattern. Flagging it at the same severity as accidental
repetition in a verse would train users to ignore repetition insights entirely.
Demotion signals "this is normal in this context" without suppressing the insight
entirely; the evidence remains visible for cases where the user wants to review.

The demotion pass runs unconditionally (even when features are not requested),
because original repetition insights on chorus sections benefit from the same context.

**Tradeoffs:**

- Demotion is applied by section label alone, not by musical intent. A song with a
  section labeled `[chorus]` that the writer intentionally made non-repetitive will
  still have its insights demoted. The user can override the label.
- Draft-scoped `word_overuse` demotion requires checking where the word appears across
  all sections. This reuses `LemmaLocation` data already built during the pass; if
  it is not requested, the word_overuse demotion is skipped for the draft scope.

---

## 13. Inner rhyme detection runs once, after sections, over the whole draft

**Decision:** While each section is analyzed, the service also collects
`(global_line_index, tokens)` for every line, using the same
`section.line_start + offset` numbering as `SectionAnalysis.line_start` /
`line_end`. After the per-section loop, `find_inner_rhyme_groups` runs once
over the entire collected list and the result is attached as the top-level
`inner_rhymes` field.

**Reasoning:**

Internal rhyme isn't bound by section: a word in a verse can rhyme with a
word in the chorus. Running the detector once over the whole draft (rather
than per-section) lets groups span section boundaries, and doing it after the
per-section loop means it can reuse the already-tokenized, already-positioned
`Token` lists without re-tokenizing.

**Tradeoffs:**

- The detector needs its own phoneme cache (`dict[str, tuple[str, ...] |
  None]`), separate from the per-request rhyme-key cache described in §3.
  The rhyme-key cache stores derived keys, not raw phonemes, so it can't be
  reused directly.
- `inner_rhymes` is always computed and always present (`[]` when nothing
  qualifies). Unlike the semantic features in §6, there is no opt-in flag or
  capability gate. See [`inner-rhyme-detection.md`](./inner-rhyme-detection.md)
  for the full grouping algorithm, confidence mapping, and ID scheme.

---

## What draft analysis does not do

- **No prosody or meter scoring.** Whether a line scans, or where the stressed syllables
  fall relative to a beat grid, is out of scope.
- **No cross-section rhyme scheme.** Rhyme scheme is computed per section. Whether
  verse and chorus share a rhyme pool is not detected.
- **No mixed-language analysis.** A draft submitted as `"en"` is analyzed entirely
  through the English pipeline, even if some lines are in Spanish.
- **No stress hints.** The `stress_hints` capability is `"unsupported"` for both
  languages currently. Spanish has deterministic stress and is the natural first
  candidate for a future implementation.
- **No embedding-backed similarity.** Section contrast and semantic repetition use
  Jaccard over content-lemma bags, which is purely lexical. Sections that use different words
  to express the same idea will not be flagged. Embedding-backed comparison is deferred
  to if golden-set analysis shows a precision gap.
- **No aspect or mood detection.** Tense drift detection covers past/present/future
  but not perfective/imperfective aspect or subjunctive/indicative mood.
