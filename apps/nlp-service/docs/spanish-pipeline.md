# Spanish Pipeline

Spanish-specific implementation details. Where English leans on a curated phoneme dictionary (CMU), Spanish leans on rules — the orthography is regular enough that rule-based G2P, syllabification, and stress get close to ground-truth without a hand-built corpus.

For the cross-language view, see [`bilingual.md`](./bilingual.md).

---

## Module layout

```text
app/domain/languages/spanish/
  engine.py          ← SpanishEngine, wires the modules into LanguageEngine
  normalization.py   ← case folding, allowed character set, junk filtering
  g2p.py             ← grapheme → phoneme (rule-based)
  syllabification.py ← rule-based syllable boundaries + nucleus tracking
  stress.py          ← stressed-syllable detection (accent or default rule)
  rhyme_rules.py     ← consonant_rhyme_key + assonant_rhyme_key
app/repositories/
  spanish_corpus.py  ← synthesizes a Pronunciation index from wordfreq + g2p
```

The engine's job is glue. Every interesting decision lives in one of the named modules.

---

## No dictionary, synthesize from frequency

**Decision:** Spanish has no `cmudict` equivalent in the Python ecosystem. The [`SpanishCorpus`](../app/repositories/spanish_corpus.py) repository synthesizes one at startup: pull the top N most-frequent Spanish tokens from `wordfreq`, normalize each, run it through the rule-based G2P, and index the result as `Pronunciation` objects. The result conforms to `PronunciationRepository`, so the same `RhymeIndex` builds it.

**Reasoning:**

Spanish G2P is regular enough that rule output is treated as canonical rather than fallback. Synthesizing from `wordfreq` gives us a coverage curve (~80,000 entries by default) tilted toward lyrically-useful vocabulary without sourcing and maintaining a custom corpus.

**Tradeoffs:**

- The corpus inherits whatever quirks `wordfreq` has — primarily web/subtitle/Wikipedia bias.
- Words below the frequency cutoff are absent from the index, so they cannot return rhymes. The G2P still works on them; the syllable count for unknown words is still exact. Only rhyme lookup degrades.
- Increasing `top_n` is the obvious knob if rhyme coverage feels thin. The cost is linear in build time and memory.

---

## Exact syllabification, not heuristic

**Decision:** [`syllabify()`](../app/domain/languages/spanish/syllabification.py) returns the canonical syllable split for any Spanish word. The engine calls it directly in `heuristic_syllable_count` rather than treating it as a dictionary-miss fallback.

**Reasoning:**

Spanish syllable boundaries follow well-defined rules around vowel clusters (hiatus vs. diphthong vs. triphthong), consonant clusters, and the special status of `y`. A rule implementation is exact for orthographically well-formed words — there is no dictionary to "miss," so the fallback framing from English does not apply.

**Tradeoff:**

The rule assumes orthographic regularity. Loanwords spelled in their source language (`shopping`, `streaming`) syllabify oddly. This is rare in lyrics and acceptable.

---

## Two rhyme kinds: consonant and assonant

**Decision:** `key_specs` declares two rhyme slots:

| Slot | Key | Match means |
| --- | --- | --- |
| `consonant` | Phonemes from the stressed vowel through the end | Same ending sound from the stressed vowel onward |
| `assonant` | Vowel phonemes from the stressed vowel through the end | Same vowel pattern from the stressed vowel onward, consonants ignored |

Both are derived from the same per-word phoneme sequence. The index builds one bucket per slot per word, so lookups for either kind cost the same.

**Reasoning:**

These are the two rhyme categories Spanish songwriting tradition cares about. "Perfect / near" is the wrong vocabulary for Spanish — the categories are not strictness levels of the same idea, they are two different ideas about what counts as a rhyme.

**Tradeoffs:**

- The web client's unified "Perfect / Near" toggle maps to `consonant / assonant` for Spanish in the client. This is a UI convenience; FastAPI does not perform the translation and will reject `perfect` for a Spanish request.
- There is no third "near consonant" tier. If that distinction matters for some songwriters, it would be a new slot, not a parameter tweak.

---

## Stress detection lives in its own module

**Decision:** [`stress.py`](../app/domain/languages/spanish/stress.py) decides which syllable is stressed. The rhyme key functions consume that index — they do not re-derive stress.

**Reasoning:**

Stress in Spanish is deterministic from spelling: an explicit accent mark (`canción`, `césped`) overrides the default rule (penultimate if the word ends in a vowel, `n`, or `s`; final otherwise). Centralizing this in one module means the rule appears once. Anywhere else that needs the stress position (e.g., a future meter feature) imports from the same place.

**Tradeoff:**

Compound words and clitics (`dímelo`, `cómpramelo`) have non-default stress patterns that the default rule alone would not catch. The accent-mark check handles this correctly for any spelling that follows RAE rules, which is the vast majority of written Spanish.

---

## Normalization is narrower than English

**Decision:** Spanish normalization keeps accent marks, `ñ`, and `ü` intact. It is permissive on input case but strict on the allowed character set (`[a-záéíóúñü']`). Hyphenated tokens are rejected at corpus build time.

**Reasoning:**

Accents carry stress information. Stripping them at normalization time would destroy the data the stress and rhyme modules need. `ñ` is a letter, not a `n + ~` combination — treating it as such would collapse minimal pairs (`año` vs. `ano`).

**Tradeoff:**

Words with non-standard apostrophes or diacritics from other languages get rejected. This is acceptable in a lyric tool — those edge cases are rarer than the harm a permissive normalizer would cause.

---

## What this pipeline does not do

- **No prosody scoring.** Whether a line scans is out of scope. The engine ships syllables and rhymes; rhythm/meter is a future concern.
- **No automatic dialect detection.** The corpus is general Spanish. Regional vocabulary (Mexican, Argentine, Castilian) is represented in `wordfreq` proportionally; the pipeline does not weight or filter by dialect.
- **No conjugation expansion.** A search for `canto` will not surface conjugated forms of `cantar` as related rhymes; the index sees them as independent words. This is what users actually want for rhyme lookup — but it would be the wrong behavior for a thesaurus feature.
