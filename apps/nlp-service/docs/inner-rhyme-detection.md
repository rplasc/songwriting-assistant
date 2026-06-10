# Inner Rhyme Detection

Design notes for `inner_rhymes`, the word-level rhyme grouping returned by
`POST /v1/analyze-line` and `POST /v1/analyze-draft`. For end-of-line rhyme
scheme (`"ABAB"`), see [`draft-analysis.md`](./draft-analysis.md#2-rhyme-scheme-assignment-keys-from-the-last-word-of-each-line).
For the rhyme-family taxonomy used by `/v1/rhymes`, see [`taxonomy.md`](./taxonomy.md).

---

## What it is

End rhyme (`rhyme_key()` + `assign_scheme`) only ever looks at the **last
word of each line**. Songwriters also rely on internal rhyme — a word in the
middle of one line echoing a word elsewhere in the same line, or in a
different line entirely. `inner_rhymes` surfaces that: every word in the
input is checked against every other word, and words that share a rhyme key
are grouped together with enough positional information for the UI to
highlight each occurrence.

```python
class RhymeOccurrence(BaseModel):
    line_index: int   # 0 for /v1/analyze-line; 1-based global line for /v1/analyze-draft
    word_index: int   # 0-based position of the word within its line
    char_start: int   # offsets into the line's raw text
    char_end: int
    text: str
    normalized: str

class InnerRhymeGroup(BaseModel):
    id: str
    rhyme_type: Literal["perfect", "near"]
    confidence: RhymeConfidence  # "high" for perfect, "medium" for near
    rhyme_key: str
    occurrences: list[RhymeOccurrence]
```

`LineAnalysisResponse.inner_rhymes` and `DraftAnalysisResponse.inner_rhymes`
both default to `[]` and are always populated (no opt-in flag, no
capability gate) — the schemas defined in
[`app/schemas/responses.py`](../app/schemas/responses.py).

---

## Where it's wired

- **`/v1/analyze-line`** ([`app/api/routes/analysis.py`](../app/api/routes/analysis.py)) —
  runs the detector over the single line's tokens with `line_index=0`. Only
  same-line groups are possible here.
- **`/v1/analyze-draft`** ([`app/services/draft_analysis_service.py`](../app/services/draft_analysis_service.py)) —
  collects `(global_line_index, tokens)` for every line across all sections
  (`section.line_start + offset`, matching the 1-based `line_start`/`line_end`
  convention used elsewhere in the draft response) and runs the detector once
  over the whole draft, so groups can span sections and lines.

Both call the same [`find_inner_rhyme_groups`](../app/domain/rhyme/inner_rhyme_rules.py),
so the grouping rules below apply identically to live (line) and structural
(draft) analysis.

---

## Token positions

`word_index`, `char_start`, and `char_end` come from
[`Token`](../app/models/token.py), populated by
[`iter_word_spans`](../app/domain/tokenization.py) during tokenization for
both the English and Spanish engines. `index` is the 0-based position among
*kept* (non-punctuation) words; `char_start`/`char_end` are byte offsets into
the raw line text, so the UI can highlight the exact substring without
re-tokenizing.

---

## Grouping algorithm

1. **Perfect pass.** Every token's phonemes are run through the language's
   perfect-rhyme key (`rhyme_key` for English, `consonant_rhyme_key` for
   Spanish) and bucketed by key.
2. **Near pass.** The same tokens are also run through the near/slant key
   (`near_rhyme_key` for English, `assonant_rhyme_key` for Spanish). Any
   occurrence whose `(line_index, word_index)` was already claimed by a
   perfect group is **excluded** — a word doesn't appear in both a perfect
   and a near group.
3. **Group filter.** A bucket only becomes a group if it has **≥ 2
   occurrences and ≥ 2 distinct normalized words**. This keeps plain word
   repetition (already covered by `repetition_rules`) from being reported as
   a rhyme.
4. **Confidence.** Perfect groups get `rhyme_type="perfect"` /
   `confidence="high"`; near groups get `rhyme_type="near"` /
   `confidence="medium"` — the same high/medium convention documented in
   [`confidence-and-evidence.md`](./confidence-and-evidence.md).
5. **Filtering noise.** Tokens with `normalized` shorter than 2 characters
   (`_MIN_WORD_LEN`) or with no resolvable phonemes are skipped entirely.
6. **Ordering.** Groups are sorted by their first occurrence
   (`line_index`, `word_index`), perfect groups before near groups on ties.

---

## Phoneme lookups

`english_phonemes_for` and `spanish_phonemes_for`
([`app/domain/rhyme/inner_rhyme_rules.py`](../app/domain/rhyme/inner_rhyme_rules.py))
mirror the per-line rhyme-key lookups already used for end-rhyme scheme
(`_english_rhyme_key` / `_spanish_rhyme_key` in `draft_analysis_service.py`):
dictionary pronunciation first, heuristic G2P fallback for English, rule-based
G2P for Spanish. Both builders take a `dict[str, tuple[str, ...] | None]`
cache keyed on the normalized word, so a draft that repeats a word many times
only computes its phonemes once per request.

---

## Deterministic IDs

Each group's `id` is `irh_` followed by the first 10 hex characters of a
SHA-1 hash of `"<language>|<rhyme_type>|<rhyme_key>|<sorted line:word positions>"`
— the same hashing pattern used for other generated IDs (`ins_`, `rhy_`).
Identical input always produces the same group IDs, which matters for the
Redis response cache and for any future client-side diffing.

---

## Cache invalidation

`/v1/analyze-draft` responses may be served from the Redis response cache
(see [`service-overview.md` §11](./service-overview.md#11-redis-response-cache-for-draft-endpoints)).
Adding `inner_rhymes` to `DraftAnalysisResponse` bumped
`NLP_CACHE_KEY_PREFIX` from `nlp:v1` to `nlp:v2`
([`app/core/config.py`](../app/core/config.py)) so previously cached
responses (which lack the field) are never served stale.

---

## What this does not do

- **No UI highlighting yet.** The gateway and web client pass `inner_rhymes`
  through to `AnalysisResult.innerRhymes` / `DraftAnalysis.innerRhymes`
  unchanged, but no component renders them yet — that is a follow-up.
- **No cross-language groups.** Each request is analyzed in one language;
  there is no attempt to rhyme an English word against a Spanish one.
- **Doesn't replace end-rhyme scheme.** `sections[].rhyme_scheme` is computed
  independently from the last word of each line, as before. A line's last
  word can appear in both its section's rhyme scheme **and** an
  `inner_rhymes` group.
- **No alliteration or consonance-only matching.** Only the perfect and
  near/slant keys already used elsewhere are reused; no new phonetic
  similarity metric was introduced.
