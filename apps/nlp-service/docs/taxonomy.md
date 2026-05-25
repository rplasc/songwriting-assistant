# Taxonomy & Phrase-Ending Rules

This document records the editorial decisions baked into the internal Phase system
of the FastAPI NLP service. It is the source of truth that PR reviewers and
future maintainers should point to before tweaking the rhyme-family
labels, the function-word lists, or the phrase-ending extractor.

parts of the document refers to "Phases" and "Milestones" that is utilized to track progress
internally.

## 1. Supported rhyme families

Every successful `/v1/rhymes` candidate carries a `rhyme_family` label
drawn from this closed taxonomy:

| Family          | Meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| `perfect`       | English perfect rhyme; full phoneme match from the last stressed vowel. |
| `multisyllabic` | Shared stressed-vowel tail spanning ≥ 2 vowels (either language).       |
| `near`          | English slant rhyme; shared vowel with similar consonants.              |
| `consonant`     | Spanish consonant rhyme (analog of English perfect).                    |
| `assonant`      | Spanish vowel-only rhyme from the last stressed vowel onward.           |

`compound_phrase` is deliberately deferred. M1 only exposes families that
the golden set demonstrates with reviewed examples.

### Family-vs-tier separation

The engine still uses internal tier names (`perfect` / `family` / `near` /
`consonant` / `assonant` / `multisyllabic`) on `RhymeCandidate.rhyme_type`
to preserve back-compat for clients that already render the tier label.
`rhyme_family` is the editorial label clients should prefer going forward.

The mapping is in
[`app/domain/rhyme/rhyme_family.py`](../app/domain/rhyme/rhyme_family.py).

## 2. Phrase-ending extraction

Phrase-ending lookups (`target_type: "phrase_ending"`) run a deterministic
trimmer before the phonetic lookup. Rules are codified in
[`app/domain/rhyme/ending_span_rules.py`](../app/domain/rhyme/ending_span_rules.py)
and tested in `tests/test_ending_span_rules.py`.

1. Take the trailing window of up to **3** tokens.
2. Strip *leading* function words from that window using the
   language-specific set (see §3).
3. If the window is entirely function words, fall back to the very last
   token as a best-effort anchor.
4. Trailing function words after a content word are kept (e.g. `hold me`
   stays `hold me`) — they contribute phonetic material to the
   concatenated tail.

The extractor never re-tokenizes; it consumes the engine's existing
`tokenize_line` output, which already applies punctuation stripping and
contraction normalization.

## 3. Function-word lists

Closed-class function words used by the trimmer:

* English — [`app/domain/languages/english/function_words.py`](../app/domain/languages/english/function_words.py).
  Articles, determiners, pronouns (including reflexives and wh-),
  auxiliaries, modals, prepositions, conjunctions, and the common
  contractions that survive `normalize_word`.
* Spanish — [`app/domain/languages/spanish/function_words.py`](../app/domain/languages/spanish/function_words.py).
  Artículos, pronombres átonos y tónicos, demostrativos, posesivos,
  preposiciones, conjunciones, interrogativos y partículas frecuentes.

Adding a word to either list should match a single editorial intent: the
word is so semantically light at the end of a sung phrase that the
rhyme target should fall through it.

## 4. Multisyllabic rhyme key

[`app/domain/rhyme/multisyllabic_rules.py`](../app/domain/rhyme/multisyllabic_rules.py)
defines `multisyllabic_rhyme_key`. It returns the phoneme tail from the
last stressed vowel **only if** that tail spans ≥ 2 vowels (default).
Otherwise it returns `None`, so words with a one-vowel stressed tail
(e.g. `cat`, `corazón`) never enter the multisyllabic index slot.

The same function is registered as a `KeySpec` on both `EnglishEngine`
and `SpanishEngine`, which means `mode="multisyllabic"` queries return
candidates whose own multisyllabic key matches the query's.

## 5. Mode defaults & capability metadata

* `target_type="word"` (default): mode falls back to the language default
  (`perfect` for English, `consonant` for Spanish).
* `target_type="phrase_ending"`: mode also falls back to the language
  default. Concatenated span phonemes naturally produce a multi-syllable
  tail when the final word's vowel is unstressed; for stressed-final
  phrases the anchor lands on the last token. Callers wanting strictly
  multi-syllable matches opt into `mode="multisyllabic"` explicitly.
* `RhymeMeta.capabilities` always reports `multisyllabic` and
  `phrase_ending` per engine (`full` for both English and Spanish in M1).

## 6. Out-of-scope (Milestones 2+)

* New ranking signals beyond family classification (e.g. diversity
  penalties, stressed-syllable bonuses for phrase endings).
* Phrase-level corpus indexing — M1 still searches a single-word index,
  so phrase-ending candidates are single words. M2 may add phrase-level
  candidates if the editorial case becomes clear.
* Lemmatization, semantic motif detection, and section contrast — all
  remain Phase 5 / M3-M4 work.
