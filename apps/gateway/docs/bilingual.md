# Bilingual Contract

How language flows through the gateway, from request validation to FastAPI dispatch to client echo. Phase 3 added language as a first-class concern; this doc records the contract so future contributors do not have to re-derive it from the code.

---

## Supported languages

Defined in [`src/common/enums/language.enum.ts`](../src/common/enums/language.enum.ts):

```ts
export const SUPPORTED_LANGUAGES = ['en', 'es'] as const;
export const DEFAULT_LANGUAGE: Language = 'en';
```

The set is intentionally narrow. Adding a language is a deliberate change — touching this enum, adding a FastAPI engine, and adding a default rhyme mode mapping — not an environment-variable toggle.

---

## Rhyme mode per language

Each language has its own valid rhyme modes:

| Language | Valid modes | Default |
| --- | --- | --- |
| `en` | `perfect`, `near` | `perfect` |
| `es` | `consonant`, `assonant` | `consonant` |

`defaultRhymeModeFor(language)` returns the default for each language. The gateway does **not** translate between vocabularies — that's a UI concern. If the client sends `perfect` for an `es` request, FastAPI will reject it (`UnsupportedModeError`) and the gateway will return an `UPSTREAM_FAILED` envelope. The web client maps its unified `perfect`/`near` toggle to the Spanish equivalents before emitting.

---

## Request flow

```text
1. Client sends    { line, language?, rhyme_mode? }
2. AnalyzeLineDto  validates language ∈ SUPPORTED_LANGUAGES
                   validates rhyme_mode ∈ SUPPORTED_RHYME_MODES
3. LanguageRequestMapper.resolve()
                   language = input.language ?? DEFAULT_LANGUAGE
                   mode     = input.rhyme_mode ?? defaultRhymeModeFor(language)
4. EditorService   forwards { line, language, mode } to FastAPI
5. FastAPI         routes via LanguageRouter → per-language engine
6. EditorResponsePresenter
                   echoes resolved { language, mode } back to client
```

The presenter echoes the resolved language and mode even when no rhymes were returned, so the client never has to remember what it asked for. If FastAPI's response includes its own resolved mode in `meta.mode`, the presenter prefers that — useful when FastAPI made a defaulting decision the gateway didn't.

---

## Why defaulting lives in the mapper, not the controller or service

[`LanguageRequestMapper`](../src/editor/mappers/language-request.mapper.ts) is a thin, single-purpose service that the HTTP controller and WebSocket gateway both call before invoking `EditorService.analyze()`. Three reasons:

- **One place to look.** If the default ever changes (e.g., a per-user preference), the change is in one file.
- **Identical behavior across transports.** Putting the default in the controller would mean HTTP and WS could drift.
- **Testable in isolation.** The mapper has no I/O and no DB — just enum logic — so it gets a fast unit-test suite without the orchestration layer's mocks.

---

## Drafts and language

Drafts carry a `language` field as part of their identity. See [`drafts.md`](./drafts.md) for the persistence contract; the short version:

- `CreateDraftDto.language` defaults to `en` when omitted.
- `UpdateDraftDto.language` is optional; passing it switches the draft's language.
- The draft's saved `language` is returned on every response via `DraftPresenter`.

The draft's language is **not** used as an implicit default for analyze requests — analyze and persist are independent surfaces. The web client carries the draft's language with each analyze request explicitly.

---

## What this contract deliberately does not do

- **No automatic language detection.** Mixed-language line analysis is explicitly out of scope for Phase 3. The gateway will not guess — if the client wants a Spanish rhyme for a Spanish line in an English draft, the client sends `language: 'es'` on the analyze call.
- **No locale negotiation.** No `Accept-Language` header parsing, no per-session locale. Language is a per-request, per-draft field, full stop.
- **No translation.** The gateway never translates content. Language is metadata that selects an analysis pipeline.

---

## When you add a third language

1. Add the code to `SUPPORTED_LANGUAGES` and decide its default rhyme mode in `defaultRhymeModeFor`.
2. Add valid rhyme modes to `SUPPORTED_RHYME_MODES` if any are new.
3. Add a FastAPI `LanguageEngine` and wire it into the `LanguageRouter` (see the NLP service's [`bilingual.md`](../../nlp-service/docs/bilingual.md)).
4. The DTO validators, defaulting mapper, and presenter pick it up automatically — no controller changes.

If step 4 is **not** true after your edit, the contract has leaked. Fix the leak before merging.
