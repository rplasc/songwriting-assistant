# Bilingual Contract

What is shared across languages, what is per-language, and what FastAPI guarantees the gateway. With Spanish added; this doc records the architecture so a future third language is a localized change rather than a refactor.

---

## The split

Three layers, each with a clear ownership rule:

| Layer | What lives here | Per-language? |
| --- | --- | --- |
| Domain (`app/domain/languages/<code>/`) | normalization, tokenization, G2P, syllabification, stress, rhyme rules, ranking modes | **yes** |
| Shared services (`app/services/`) | rhyme index, syllable service, rhyme service, ranking, pronunciation service | no — depends on the `LanguageEngine` interface only |
| Routing (`app/services/language_router.py`) | maps `language` code → `LanguageContext` (engine + repo + index + services) | no — but configured per language at startup |

The shared services never branch on language. Anything that needs to differ between languages lives behind the [`LanguageEngine`](../app/domain/languages/base.py) abstract class.

---

## What the engine owns

```python
class LanguageEngine(ABC):
    code: str
    supported_modes: tuple[str, ...]
    default_mode: str
    key_specs: tuple[KeySpec, ...]
    match_reasons: dict[str, str]

    def normalize_word(...)
    def tokenize_line(...)
    def heuristic_syllable_count(...)
    def frequency(...)
    def is_corpus_eligible_word(...)
    def candidate_tiers(...)
    def heuristic_candidates(...)  # default: empty
    def validate_mode(...)

    # Ranking hooks — concrete methods with safe defaults so subclasses opt in:
    def is_same_stem_inflection(query, candidate) -> bool  # default: False
    def shares_stem(query, candidate, min_stem=4) -> bool  # default: prefix-overlap
    def stress_signature(word) -> str | None               # default: None (disabled)
```

`is_same_stem_inflection` and `shares_stem` are called per candidate inside `score_entries`. Returning True applies the inflection (−0.20) or same-stem (−0.10) penalty. English overrides `is_same_stem_inflection` with the original English suffix logic. Spanish overrides both with Spanish morphology (verb paradigms, gender/number pairs) and `stress_signature` (aguda / llana / esdrújula), adding a +0.03 bonus when query and candidate share stress class.

If you find yourself adding `if engine.code == "es":` somewhere in shared code, the engine interface has gaped. Add a method to the interface instead.

---

## Spanish corpus composition

The Spanish corpus is built from two sources merged at startup:

1. **wordfreq top-150k** — the 150,000 most frequent Spanish tokens from the wordfreq "es" dataset (raised from the original 80k for wider poetic/regional coverage).
2. **PR/Reggaetón slang** — a curated hand-tuned list (`app/domain/languages/spanish/data/pr_slang.py`) with ~80 entries. Words already covered by wordfreq are skipped; the slang list only fills gaps. Synthetic frequencies are assigned in the `1e-7..3e-5` band, above `CORPUS_FREQ_FLOOR` so entries survive filtering and below common Spanish nouns so they don't crowd ranking.

`SpanishEngine.frequency()` returns `max(wordfreq, slang_floor)` so the corpus build and the ranker see the same frequency floor.

## Assonant-tier policy

In **consonant mode** (cascade), the assonant secondary tier subtracts the consonant set so each word appears only once. In **assonant mode** (standalone), the full assonant set is returned without subtraction. This gives a richer candidate pool when the user explicitly asks for vowel-pattern matches.

## The startup lifespan

For each supported language, the FastAPI `lifespan` hook builds a `LanguageContext`:

```text
PronunciationRepository  →  RhymeIndex (built from repo + engine.key_specs)
                                │
                                ▼
                        PronunciationService
                                │
                                ▼
                      SyllableService, RhymeService
```

All seven of those are owned by the language: switching from English to Spanish picks up a different repository, a different index, and per-language service instances. The router stores the bundle as a `LanguageContext` dataclass.

This is intentional duplication. The alternative, sharing service instances across languages and passing a language argument through every method, was rejected because it would have meant every service method took a `LanguageEngine` parameter, every test setup had to provide one, and every cache key had to compose with it. The bundle-per-language approach concentrates the per-language plumbing at startup and lets the request path stay clean.

---

## What the gateway sees

Every successful response includes a resolved language and a resolved mode in `meta`:

```json
{
  "line": "...",
  "syllables": { "total": 8, "tokens": [...] },
  "rhymes": [...],
  "meta": {
    "request_id": "...",
    "language": "es",
    "mode": "consonant",
    "latency_ms": 42
  }
}
```

The gateway echoes both back to the client. The client never has to remember what it asked for; the response is self-describing.

---

## Modes per language

Mode validity is engine-owned and enforced inside the engine via `validate_mode`. If the request specifies an unsupported mode for the resolved language, FastAPI raises `UnsupportedModeError`, which surfaces as a `validation_error` envelope to the gateway:

| Language | Modes | Default |
| --- | --- | --- |
| English | `perfect`, `near` | `perfect` |
| Spanish | `consonant`, `assonant` | `consonant` |

The gateway is **not** responsible for translating between vocabularies. If the UI wants to expose a unified "strict / loose" toggle, the translation happens client-side before the request leaves the browser. FastAPI rejects cross-language modes rather than silently coercing them: silent coercion would hide real bugs in the request path.

---

## Draft analysis capability contract

Each feature is reported in the `capabilities` object of every `POST /v1/analyze-draft` response. The level is one of
`"unsupported"`, `"partial"`, or `"full"`.

| Capability | English | Spanish | Notes |
| --- | --- | --- | --- |
| `rhyme_scheme` | `full` | `full` | always returned |
| `syllable_analysis` | `full` | `full` | always returned |
| `cadence` | `full` | `full` | always returned |
| `repetition` | `full` | `full` | always returned |
| `semantic_repetition` | `full` | `full` | opt-in |
| `motif_tracking` | `full` | `full` | opt-in |
| `section_contrast` | `full` | `full` | opt-in |
| `consistency_hints` | `full` | `partial` | opt-in — ES is `partial` because simplemma mis-lemmatizes common irregular verbs (ser, ir, haber), making tense detection unreliable for ES. Pronoun-drift detection would be `full` in both, but the umbrella field reflects the weakest sub-feature. |

Capabilities that are not requested default to `"unsupported"` in the response regardless
of language, so clients can check the value without knowing the request options.

---

## What this contract deliberately excludes

- **No automatic language detection.** The router refuses to guess. If the gateway doesn't provide `language`, the gateway's default takes over (currently `en`).
- **No mixed-language line analysis.** A single request analyzes the line through one engine. A request that mixes English and Spanish in one line gets analyzed as whichever language was specified; the wrong-language tokens will produce low-confidence results (English heuristic) or get rejected by the normalization filter (Spanish).
- **No cross-language rhymes.** A Spanish word will never appear as a rhyme suggestion for an English query, even if the phonemes happen to align. Cross-language rhyming would require a phoneme normalization layer that does not exist.

---

## Adding a third language

1. Create `app/domain/languages/<code>/` with: `engine.py`, plus whatever modules (normalization, syllabification, g2p, rhyme_rules) you need.
2. Implement `LanguageEngine`. Pay particular attention to `key_specs`: the slot names become the wire `rhyme_type` values.
3. Create a `PronunciationRepository` implementation for the new language. If there is no dictionary, follow the Spanish pattern: synthesize from a frequency corpus + your G2P.
4. In the FastAPI `lifespan`, build the repository, build the index (driven by `engine.key_specs`), build the services, and register a new `LanguageContext` with the router.
5. Update the gateway's [`bilingual.md`](../../gateway/docs/bilingual.md) and `SUPPORTED_LANGUAGES` enum to match.

No edits to shared services should be required. If they are, the engine interface needs to grow.

See [`language-routing.md`](./language-routing.md) for the request-time view and [`spanish-pipeline.md`](./spanish-pipeline.md) for the Spanish implementation as a worked example.
