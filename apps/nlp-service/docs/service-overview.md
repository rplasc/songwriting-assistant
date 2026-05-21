# NLP Service — Design Decisions and Tradeoffs

## Purpose

This document records the significant design decisions that shape the FastAPI rhyme and syllable engine. The original decisions from the English-only build still hold — they are recorded here as they apply across both languages. Spanish-specific and routing-specific decisions are split into their own files and linked at the end.

---

## 1. Engine-per-language behind a single interface

**Decision:** Both languages implement the [`LanguageEngine`](../app/domain/languages/base.py) abstract class. The router selects an engine by code; the rhyme index, syllable service, and rhyme service depend on the interface, not on any specific language.

**Reasoning:**

Branching on language inside the shared services would have meant `if code == "en"` checks scattered through normalization, tokenization, rhyme-key derivation, and ranking. The engine-per-language pattern collapses all of that into one polymorphic dispatch at the routing edge, keeping the shared services free of language conditionals.

**Tradeoffs:**

- Adding a language is a real change — a new engine module, a new repository, a new context registration in the lifespan. There is no "configuration toggle" path.
- Two engines mean two indexes in memory. Memory grows linearly with supported languages. Currently ~80 MB for English + ~25 MB for Spanish; acceptable for the foreseeable future.

See [`language-routing.md`](./language-routing.md) for how requests flow through the router.

---

## 2. CMU Pronouncing Dictionary as the English source of truth

**Decision:** Use the `cmudict` Python package to load the Carnegie Mellon Pronouncing Dictionary at startup. Access is encapsulated behind a `PronunciationRepository` abstraction so the backing source can be swapped later.

**Reasoning:**

The CMU dict covers ~126,000 English words with ARPABET phoneme sequences, is fully deterministic, requires no network calls, and loads in well under a second. It has been the standard academic and commercial baseline for English pronunciation tasks for decades, making it easy for future maintainers to reason about.

**Tradeoffs:**

- Unknown words get no dictionary pronunciation, so rhymes cannot be suggested for invented words, proper nouns, or very recent vocabulary. The heuristic syllable fallback and the tail-only spelling heuristic in `english.engine.heuristic_candidates` mitigate partial degradation; rhyme quality on unknowns is best-effort.
- The dictionary was last updated around 2015. New words and internet slang are absent. A grapheme-to-phoneme (G2P) model such as `g2p-en` or `phonemizer` would improve coverage but adds inference latency and a non-deterministic element. Out of scope.
- The abstraction boundary (`PronunciationRepository`) is the swap point for this decision. A CMU + G2P fallback could be added without touching routes, services, or the rhyme index.

---

## 3. In-memory reverse rhyme index built once at startup

**Decision:** At startup, every (word, pronunciation) pair from each language's source is walked once, rhyme keys are extracted per pronunciation, and a `dict[rhyme_key, set[word]]` reverse map is built entirely in memory. Rhyme lookups are constant-time hash reads after that.

**Reasoning:**

Building the full reverse index takes a few seconds per language on a typical laptop and is amortised across the service lifetime. Retrieval of rhymes for a word is then O(|pronunciations|) hash lookups plus a set union, well within the 200 ms interactive target.

**Tradeoffs:**

- Memory cost as noted above.
- The index is immutable after startup. Adding a user-supplied pronunciation or custom word requires a restart. This is fine for now and keeps the concurrency story trivial (no locking needed at read time).
- Building at startup means the first request is always fast. A lazy-build approach would reduce startup time but introduce inconsistent latency on early requests, which is worse for interactive use.

---

## 4. Rhyme key definitions are engine-owned

**Decision:** Each engine declares its own `key_specs` — named slots (`perfect`, `near`, `consonant`, `assonant`) whose key functions take a phoneme sequence and return a string. The `RhymeIndex` builds one bucket per slot per word.

**Reasoning:**

The English notion of a perfect rhyme (ARPABET phonemes from the last stressed vowel) and the Spanish notion of a consonant rhyme (graphemic ending from the stressed vowel) are linguistically distinct — they should be defined where the linguistics live, not in shared infrastructure. The slot-name → match-reason mapping lives on the engine for the same reason.

**Tradeoffs:**

- Engines that share key logic (e.g., two Romance languages with overlapping rhyme rules) would re-implement that logic. A `shared/` module for cross-language helpers could be added if duplication becomes painful.
- The slot name is also the `rhyme_type` returned to the client. Renaming a slot is an API change.

See [`spanish-pipeline.md`](./spanish-pipeline.md) for the Spanish key definitions and [`bilingual.md`](./bilingual.md) for the cross-cutting view.

---

## 5. Determinism over cleverness in ranking

**Decision:** Rhyme candidates are sorted by tier (per the engine's `candidate_tiers`), then by corpus frequency (descending), then alphabetically. Abbreviations and shape-illegal tokens are filtered before scoring.

**Reasoning:**

Frequency is provided by `wordfreq` for both languages, which gives reasonably "common-feeling" words ahead of obscure ones without requiring a custom corpus. Within a frequency tie, alphabetical ordering makes the output stable across identical requests — useful for debugging and for any downstream UI that caches results.

**Tradeoffs:**

- `wordfreq`'s frequencies come from web/subtitle/Wikipedia corpora, which do not perfectly match lyric vocabulary. A music-specific corpus would surface lyric-natural words better; the cost is sourcing and maintaining that corpus.
- Alphabetic stability means the service will return rhymes in a predictable order that may not match a songwriter's intuition about which rhyme is most useful. This is intentional: the UI can re-sort, but the service should never be surprising without a good reason.

---

## 6. Heuristic syllable fallback for unknown English words

**Decision:** When an English word is absent from the CMU dict, syllable count falls back to a vowel-group heuristic. Spanish does not need a fallback — Spanish syllabification is rule-based and exact.

**Reasoning:**

For English, returning 0 or an error for unknown words would degrade the line-analysis endpoint for any line containing a proper noun, neologism, or typo. A rough count is almost always more useful than a hard failure — the songwriter can see that the total is approximate and adjust.

For Spanish, the syllabification rule is the primary source — there is no dictionary to miss. The engine calls `syllabify(word)` directly in `heuristic_syllable_count`.

**Tradeoffs:**

- The English heuristic is wrong on many words. `beautiful` has 4 vowel groups but 3 syllables; `queue` has 3 vowel letters but 1 syllable. A purpose-built G2P model would be more accurate. The heuristic is a placeholder that buys coverage at low cost.
- `low_confidence: true` is returned alongside heuristic counts so the UI (and NestJS) can signal lower confidence. The data is transparent about its own reliability.

---

## 7. Four focused endpoints rather than a combined `POST /v1/analyze`

**Decision:** The service exposes four endpoints — `GET /healthz`, `POST /v1/rhymes`, `POST /v1/analyze-line`, and `POST /v1/analyze-draft` — instead of a combined endpoint that returns everything in one call.

**Reasoning:**

Each endpoint has a distinct caller and a distinct trigger in the UI: syllable analysis fires on keystroke (or on pause); rhyme lookup fires only when the user explicitly requests suggestions for a word; draft analysis fires when the user saves or requests a structural review of the full draft. Combining them would force rhyme lookup on every line-analysis call and draft-level work on every word query — unnecessary computation and latency in all cases.

Keeping them separate also makes each endpoint independently testable and keeps each service class focused on one responsibility. The draft analysis endpoint in particular aggregates across all lines and sections in one call; coupling it to per-word rhyme lookup would produce awkward request shapes.

**Tradeoffs:**

- If a future UI feature requires rhymes and line analysis in a single round-trip, NestJS would need to issue two parallel requests or the service would need an aggregated endpoint added. The aggregated endpoint can be added without touching existing routes.

See [`draft-analysis.md`](./draft-analysis.md) for the design decisions specific to `POST /v1/analyze-draft`.

---

## 8. Services and repositories stored on `app.state`; injected via `Depends`

**Decision:** Repositories, indexes, and service objects are constructed once per language in the FastAPI `lifespan` context and stored on `app.state`. Routes retrieve them via `Depends(lambda req: req.app.state.X)`.

**Reasoning:**

FastAPI's dependency injection works well for per-request objects, but the dictionaries, indexes, and engines are process-global singletons: creating them per-request would be catastrophically slow (1–3 seconds per call). Storing them on `app.state` is the idiomatic FastAPI pattern for this case, keeps service classes free of FastAPI imports, and makes them trivially replaceable in tests via `TestClient`.

**Tradeoffs:**

- `app.state` is untyped; a typo in the attribute name fails at runtime rather than at import time. A typed `AppState` dataclass could be attached at startup instead, but adds boilerplate that is not justified at this scale.
- The pattern does not support hot-reloading dictionaries without a full process restart. That is intentional — dictionaries are immutable data and hot-reload would require locking the index during rebuild.

---

## 9. Uniform error envelope for all 4xx / 422 responses

**Decision:** A custom exception handler converts FastAPI's default validation error and HTTP exception shapes into a single envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request payload failed validation.",
    "details": [...]
  }
}
```

Pydantic v2 stores the underlying Python exception object in the error `ctx` dict; the handler uses `jsonable_encoder` with a custom `Exception → str` serialiser to avoid a `TypeError` when serialising those details.

**Reasoning:**

NestJS needs to parse error responses reliably. FastAPI's default 422 shape (`{"detail": [...]}`) differs from its default HTTP error shape (`{"detail": "..."}`), which would force NestJS to handle two different error formats. A single envelope simplifies the integration contract.

The `UnsupportedLanguageError` and `UnsupportedModeError` raised by the language router and engines surface through the same envelope with stable codes that NestJS branches on.

**Tradeoffs:**

- Wrapping errors adds one level of JSON nesting that callers must unwrap. Standard practice in REST APIs.
- The `details` array preserves Pydantic's full validation context (field path, error type, input value), which is verbose but useful for debugging. A production-grade API might strip `input` from validation details to avoid echoing user data in error logs.

---

## Further reading

- [`bilingual.md`](./bilingual.md) — the cross-cutting language contract: what is shared, what is per-language, what FastAPI guarantees the gateway.
- [`language-routing.md`](./language-routing.md) — how the `LanguageRouter` dispatches each request to the right engine.
- [`spanish-pipeline.md`](./spanish-pipeline.md) — Spanish-specific decisions: rule-based G2P, syllabification, stress, the synthesized corpus, and the consonant/assonant rhyme definitions.
- [`draft-analysis.md`](./draft-analysis.md) — design decisions for `POST /v1/analyze-draft`: section parsing, rhyme scheme assignment, cadence classification, and repetition detection.
