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

---

## 1. Section parsing: explicit beats heuristic

**Decision:** If the request includes a `sections` array, the service maps each section
directly to the named line ranges in `content`. If sections are omitted, the service
falls back to heuristic parsing in
[`section_parser.py`](../app/domain/draft_analysis/section_parser.py), which splits
on blank lines and infers labels from header-like text ("Verse 1:", "Chorus", etc.).

**Reasoning:**

The web client already has a structured view of the draft — it knows which lines belong
to which section and has assigned labels. Sending that structure with the request costs
nothing and lets the service skip a fragile heuristic entirely.

The heuristic exists because not all callers will have structured section data. A plain
text submission (curl, future integrations) should still produce a useful response
rather than a validation error.

**Tradeoffs:**

- When the client provides sections, `line_start` / `line_end` must refer to
  1-indexed lines in `content`. Off-by-one errors in the client become silent
  wrong-section assignments rather than errors — the service trusts the caller's
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
  treats `None` as a wildcard — it does not create a rhyme class for it. This degrades
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
  allow reuse across the rhyme scheme and repetition modules — not worth it yet.
- The cache is not bounded. A pathological draft with 64 unique end words would hold
  64 entries. At current limits (64 sections × ~80 lines max) this is irrelevant.

---

## 4. Cadence classification from syllable variance

**Decision:** [`classify_pattern`](../app/domain/draft_analysis/cadence_rules.py)
takes the list of per-line syllable counts for a section and returns a `CadenceResult`
with a `cadence_class` (`"consistent"`, `"mixed"`, or `"varied"`), a variance float,
and a pre-formatted severity message for the insights list.

Section label is also passed so that chorus and hook sections can apply looser variance
thresholds — structured repetition in a hook is not a problem.

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
verse — the section-level pass can account for the label. Word overuse ("love" on 10 of
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
  — both are worth surfacing — but it can produce a noisy insights list for highly
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
