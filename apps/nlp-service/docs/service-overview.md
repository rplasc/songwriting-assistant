# NLP Service — Design Decisions and Tradeoffs

## Purpose

This document records the significant design decisions made during the Phase 1
implementation of the FastAPI rhyme engine, including the reasoning behind each
choice and what was deliberately traded away.

---

## 1. CMU Pronouncing Dictionary as the Single Source of Truth

**Decision:** Use the `cmudict` Python package to load the Carnegie Mellon
Pronouncing Dictionary at startup. Access is encapsulated behind a
`PronunciationRepository` abstraction so the backing source can be swapped
later.

**Reasoning:**

The CMU dict covers ~126 000 English words with ARPABET phoneme sequences, is
fully deterministic, requires no network calls, and loads in well under a
second. It has been the standard academic and commercial baseline for English
pronunciation tasks for decades, making it easy for future maintainers to
reason about.

**Tradeoffs:**

- Unknown words get no pronunciation, so rhymes cannot be suggested for
  invented words, proper nouns, or very recent vocabulary. The heuristic
  syllable fallback mitigates partial degradation (the line-analysis endpoint
  still returns a count), but rhyme suggestions silently return an empty list.
- The dictionary was last updated around 2015. New words and internet slang are
  absent. A grapheme-to-phoneme (G2P) model such as `g2p-en` or `phonemizer`
  would improve coverage but adds inference latency and a non-deterministic
  element. That extension is explicitly out of scope for Phase 1.
- The abstraction boundary (`PronunciationRepository`) is the swap point for
  this decision. A CMU + G2P fallback could be added without touching routes,
  services, or the rhyme index.

---

## 2. In-Memory Reverse Rhyme Index Built Once at Startup

**Decision:** At startup, every (word, pronunciation) pair from the CMU dict is
walked once, a rhyme key is extracted per pronunciation, and a
`dict[rhyme_key, set[word]]` reverse map is built entirely in memory. Rhyme
lookups are constant-time hash reads after that.

**Reasoning:**

The CMU dict is ~15 MB of data. Building the full reverse index takes roughly
1–3 seconds on a typical laptop and is amortised across the service lifetime.
Retrieval of rhymes for a word is then O(|pronunciations|) hash lookups plus a
set union, well within the 200 ms interactive target per the spec.

**Tradeoffs:**

- Memory usage is approximately 50–80 MB for the index (alongside the raw
  dictionary), which is acceptable for a sidecar service. If memory ever
  becomes a constraint, the index could be serialised to a SQLite file at build
  time and loaded as a read-only mmap — but that is premature for Phase 1.
- The index is immutable after startup. Adding a user-supplied pronunciation or
  custom word requires a restart. This is fine for Phase 1 and keeps the
  concurrency story trivial (no locking needed at read time).
- Building the index at startup means the first request is always fast. An
  alternative lazy-build approach would reduce startup time but introduce
  inconsistent latency on early requests, which is worse for interactive use.

---

## 3. Rhyme Key Definition: Last Stressed Vowel to End

**Decision:** The rhyme key for a pronunciation is the ARPABET phoneme sequence
starting from the **last stressed vowel** (a phoneme whose trailing digit is
`1` or `2`) through the end of the sequence, joined with underscores. If no
stressed vowel exists, the last vowel of any stress level is used as the
fallback start.

**Reasoning:**

This is the standard linguistic definition of a perfect rhyme suffix ("the
rhyme" in syllable-structure terms: the vowel nucleus plus any trailing
consonants). Starting from the last stress marker ensures that multi-syllable
words rhyme on their dominant syllable — e.g., `fire` (AY1\_ER0) matches
`higher` (AY1\_ER0) but not `liar` on a different stress (LY1\_ER0).

**Tradeoffs:**

- Words with multiple pronunciations generate multiple rhyme keys. A word
  appears in the index under each key, which means some near-rhymes can show
  up in perfect-rhyme results if a candidate word has one pronunciation that
  shares the key with an alternate pronunciation of the input. This is rare but
  real. Phase 1 accepts this because the CMU dict's alternate pronunciations
  are typically very close (e.g., unstressed vs. stressed variants), so the
  practical quality impact is small.
- This definition produces **perfect rhymes only** — it does not capture
  family rhymes, slant rhymes, or assonance. Song lyrics frequently use these.
  Near-rhyme support is designed in (the `include_near` flag is accepted by the
  API and forwarded through `meta`) but is inert in Phase 1, so NestJS can
  pass the flag without a breaking API change when the feature lands.

---

## 4. Determinism Over Cleverness in Ranking

**Decision:** Rhyme candidates are sorted by word length ascending, then
alphabetically. Abbreviations and tokens containing non-alphabetic characters
are filtered before sorting.

**Reasoning:**

Shorter words tend to feel more natural in lyrics, and alphabetic ordering
makes the output stable across identical requests — useful for debugging and
for any downstream UI that caches results. This approach requires zero ML
infrastructure and produces consistent, reviewable output.

**Tradeoffs:**

- A corpus-frequency proxy (e.g., word frequency from a subtitle corpus) would
  surface common words like `hire` before obscure ones like `eir`. Frequency
  ranking is the obvious next upgrade but requires an additional data source
  and raises questions about which corpus reflects lyric vocabulary.
- Alphabetic stability means the service will always return `dire` before
  `entire` before `fire` — which may not match a songwriter's intuition about
  which rhyme is most useful. This is intentional: the UI can re-sort, but the
  service should never be surprising without a good reason.
- The non-alpha filter (`is_clean_word`) removes single-letter entries and
  tokens with dots or digits. This drops some legitimate results (e.g., `it's`)
  because CMU dict includes contracted forms inconsistently. This is a known
  limitation documented in the spec.

---

## 5. Heuristic Syllable Fallback for Unknown Words

**Decision:** When a word is absent from the CMU dict, syllable count falls
back to a vowel-group heuristic: count vowel groups (`[aeiouy]+`), subtract
one for a silent trailing `e` (when the word has more than one syllable), and
enforce a minimum of 1.

**Reasoning:**

Returning 0 or an error for unknown words would degrade the line-analysis
endpoint for any line containing a proper noun, neologism, or typo. A rough
count is almost always more useful than a hard failure — the songwriter can see
that the total is approximate and adjust.

**Tradeoffs:**

- The heuristic is wrong on many words. `beautiful` has 4 vowel groups but 3
  syllables; `queue` has 3 vowel letters but 1 syllable. A purpose-built G2P
  model would be far more accurate for unknowns. The heuristic is a placeholder
  that buys coverage at low cost.
- `pronunciation_found: false` is always returned alongside heuristic counts so
  the UI (and NestJS) can signal lower confidence. The data is transparent
  about its own reliability.
- Because the heuristic is only reached for unknown words, it does not affect
  the accuracy of the common-word path, which routes through the CMU dict and
  is exact.

---

## 6. Separate `POST /v1/rhymes` and `POST /v1/analyze-line` Endpoints

**Decision:** Rhyme lookup and line analysis are separate endpoints rather than
a combined `POST /v1/analyze` that returns both in one call.

**Reasoning:**

The two operations have different callers and different trigger conditions in
the planned UI: syllable analysis fires on every keystroke (or on pause), while
rhyme lookup fires only when the user explicitly requests suggestions for a
specific word. Combining them would force the rhyme lookup on every analysis
request, wasting work and latency.

Keeping them separate also makes each endpoint independently testable and keeps
each service class focused on one responsibility.

**Tradeoffs:**

- If a future UI feature requires both in a single round-trip (e.g., opening a
  rhyme panel at the same time as analysing a line), NestJS would need to issue
  two parallel HTTP requests or the service would need the combined endpoint
  added. The spec anticipates this as `POST /v1/analyze` and explicitly defers
  it to when the UI path is clearer. The combined endpoint can be added without
  touching existing routes.

---

## 7. Services and Repositories Stored on `app.state`; Injected via `Depends`

**Decision:** The `CmuDictRepository`, `RhymeIndex`, and all service objects
are constructed once in the FastAPI `lifespan` context and stored on
`app.state`. Routes retrieve them via `Depends(lambda req: req.app.state.X)`.

**Reasoning:**

FastAPI's dependency injection works well for per-request objects, but the
dictionary and index are process-global singletons: creating them per-request
would be catastrophically slow (1–3 seconds per call). Storing them on
`app.state` is the idiomatic FastAPI pattern for this case, keeps service
classes free of FastAPI imports, and makes them trivially replaceable in tests
via `TestClient` (which runs the lifespan hook once per session fixture).

**Tradeoffs:**

- `app.state` is untyped; a typo in the attribute name fails at runtime rather
  than at import time. This is a minor ergonomics cost. A typed `AppState`
  dataclass could be attached at startup instead, but adds boilerplate that is
  not justified at this scale.
- The pattern does not support hot-reloading the dictionary without a full
  process restart. That is intentional: the dictionary is immutable data, and
  hot-reload would require locking the index during rebuild, which is not worth
  the complexity in Phase 1.

---

## 8. Uniform Error Envelope for All 4xx / 422 Responses

**Decision:** A custom exception handler converts FastAPI's default validation
error and HTTP exception shapes into a single envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request payload failed validation.",
    "details": [...]
  }
}
```

Pydantic v2 stores the underlying Python exception object in the error `ctx`
dict; the handler uses `jsonable_encoder` with a custom `Exception → str`
serialiser to avoid a `TypeError` when serialising those details.

**Reasoning:**

NestJS needs to parse error responses reliably. FastAPI's default 422 shape
(`{"detail": [...]}`) differs from its default HTTP error shape
(`{"detail": "..."}`), which would force NestJS to handle two different error
formats. A single envelope simplifies the integration contract.

**Tradeoffs:**

- Wrapping errors adds one level of JSON nesting that callers must unwrap. This
  is standard practice in REST APIs and is a minor cost compared to the benefit
  of a consistent contract.
- The `details` array preserves Pydantic's full validation context (field path,
  error type, input value), which is verbose but useful for debugging. A
  production-grade API might strip `input` from validation details to avoid
  echoing user data in error logs — that is a hardening step for a later pass.
