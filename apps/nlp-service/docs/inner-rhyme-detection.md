# Inner Rhyme Detection

Design notes for `inner_rhymes`, the word-level rhyme grouping returned by
`POST /v1/analyze-line` and `POST /v1/analyze-draft`. For end-of-line rhyme
scheme (`"ABAB"`), see [`draft-analysis.md`](./draft-analysis.md#2-rhyme-scheme-assignment-keys-from-the-last-word-of-each-line).
For the rhyme-family taxonomy used by `/v1/rhymes`, see [`taxonomy.md`](./taxonomy.md).

---

## What it is

End rhyme (`rhyme_key()` + `assign_scheme`) only ever looks at the **last
word of each line**. Songwriters also rely on internal rhyme: a word in the
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
capability gate), per the schemas defined in
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

The detector is tuned for **scheme clarity over raw recall**: early testing
against dense rap lyrics showed that pure bucketing highlighted nearly every
word (function words, incidental vowel matches) and drowned the primary
scheme in color. Three deliberate filters implement the
"weight end-of-line delivery over mid-sentence functional matches" principle.

1. **Token filter.** Tokens with `normalized` shorter than 2 characters
   (`_MIN_WORD_LEN`) or with no resolvable phonemes are skipped entirely.
   The last surviving token of each line is marked **line-final**, and each
   token's syllable count (max vowel count across pronunciation variants) is
   recorded — both feed the anchor rules below.
2. **Perfect pass.** Every token's phonemes are run through the language's
   perfect-rhyme key (`rhyme_key` for English, `consonant_rhyme_key` for
   Spanish) and bucketed by key.
   A `_FUNCTION_WORDS` token ("my", "to", "the", …) enters a bucket only
   when it is line-final. A line *ending* on "you"/"do" is a real end-rhyme;
   mid-line function-word matches are cognitive noise.
3. **Cadence pass (English only).** Words not claimed by a perfect group are
   bucketed by
   [`ending_cadence_key`](../app/domain/rhyme/ending_cadence_rules.py) —
   syllable count from the last *primary* stress, reduced final rime, manner
   class of the closing consonant — which connects multisyllabic deliveries
   that rhyme *rhythmically* even when their phonemes differ
   ("sandwiches"/"allowances"/"analysts"/"counterfeits" all key `3_x_fric`).
   Candidacy is position-independent: the key's 3-beat minimum means only
   long deliveries qualify, so mid-line "sandwiches" still joins. Each line
   also contributes a **compound ending span** — trailing function words
   joined (destressed) onto the content word carrying the final stress — so
   "countin' *this*" / "downin' *this*" rhyme as units, every word in the
   span highlighted together. This pass runs *before* the near tier so a
   delivery family isn't split by one member being claimed into an unrelated
   slant group first. Groups are emitted as `rhyme_type="near"`.
4. **Near pass.** Remaining tokens are run through the strict inner slant
   key (`inner_near_rhyme_key` for English — anchored on the last *primary*
   stress so compounds like "paystub" match the "waist" family —
   `assonant_rhyme_key` for Spanish). Any occurrence already claimed by a
   perfect or cadence group is **excluded**: a word appears in at most one
   group. Function words never enter this pass.
5. **Group filter.** A bucket only becomes a group if it has **≥ 2
   occurrences and ≥ 2 distinct normalized words**. This keeps plain word
   repetition (already covered by `repetition_rules`) from being reported as
   a rhyme — with one exception: an **end-refrain**, the same content word
   ending two or more lines ("…funk" / "…funk"), is the structural anchor of
   its bars and is kept as a perfect group. All-function-word buckets are
   additionally suppressed in the near tier ("them"/"then" is noise, not
   craft), and a repeated line-final *function* word is not a refrain.
6. **Anchor pruning.** A group survives only if it contains at least
   one line-final occurrence **or** one occurrence with
   `_ANCHOR_MIN_SYLLABLES` (2) or more syllables. Perfect groups may
   alternatively survive as a dense chain of
   `_DENSE_GROUP_MIN_DISTINCT_WORDS` (3) or more *distinct* words — a
   mid-line cat/sat/mat run is deliberate craft, while sit/quit/quit
   (repeats padding the count) is not. Near groups get no dense escape
   hatch: scattered mid-line monosyllable slant matches are the dominant
   highlight noise.
7. **Confidence.** Perfect groups get `rhyme_type="perfect"` /
   `confidence="high"`; cadence and near groups get `rhyme_type="near"` /
   `confidence="medium"`, the same high/medium convention documented in
   [`confidence-and-evidence.md`](./confidence-and-evidence.md). The web
   client renders `near` groups de-emphasized (fainter marker wash, dashed
   underline) so the perfect scheme visually dominates.
8. **Ordering.** Groups are sorted by their first occurrence
   (`line_index`, `word_index`), perfect groups before near groups on ties.

**Rejected alternatives**, recorded so they aren't re-proposed:

- *A hard top-N group cap.* Ranking reshuffles as the user types, which makes
  highlights flicker between analyses; the deterministic anchor rules don't.
- *CMU stress digits for function-word detection.* CMU marks "my"/"to" with
  primary stress, so the lexical `_FUNCTION_WORDS` list is more reliable than
  phonetics here. (For the same reason, function words joined into a compound
  span are destressed before keying.)
- *Restricting the cadence pass to line-final words.* First tried; it missed
  mid-line members of a delivery family ("syrup **sandwiches** and crime
  allowances") and could not represent compound units at all. The 3-beat
  minimum replaced position as the noise guard.

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
, the same hashing pattern used for other generated IDs (`ins_`, `rhy_`).
Identical input always produces the same group IDs, which matters for the
Redis response cache and for any future client-side diffing.

---

## Cache invalidation

`/v1/analyze-draft` responses may be served from the Redis response cache
(see [`service-overview.md` §11](./service-overview.md#11-redis-response-cache-for-draft-endpoints)).
Adding `inner_rhymes` to `DraftAnalysisResponse` bumped
`NLP_CACHE_KEY_PREFIX` from `nlp:v1` to `nlp:v2`; the scheme-clarity tuning
bumped it to `nlp:v3`, and the cadence/refrain revision to `nlp:v4`
([`app/core/config.py`](../app/core/config.py)) so previously cached
responses are never served stale.

---

## What this does not do

- **No cross-language groups.** Each request is analyzed in one language;
  there is no attempt to rhyme an English word against a Spanish one.
- **Doesn't replace end-rhyme scheme.** `sections[].rhyme_scheme` is computed
  independently from the last word of each line, as before. A line's last
  word can appear in both its section's rhyme scheme **and** an
  `inner_rhymes` group.
- **No alliteration or consonance-only matching.** Only the perfect,
  near/slant, and line-ending cadence keys are used; no general phonetic
  similarity metric was introduced.
- **No multi-word ending spans.** `ending_span_rules` and
  `multisyllabic_rules` remain wired into the `/v1/rhymes` suggestion path
  only; matching multi-word line endings ("taste bloods" / "paystub") as
  highlight groups is future work.

(The gateway and web client render `inner_rhymes` as in-editor highlights:
color slot hashed from `rhyme_key`, `near` groups de-emphasized. See
`apps/web/src/features/editor/tiptap/inner-rhyme-extension.ts`.)
