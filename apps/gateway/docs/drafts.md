# Drafts Module

The drafts module owns draft persistence for the songwriting workspace. It exposes a REST CRUD surface, validates inputs against the bilingual language contract, and presents stable client-facing payloads. The module currently ships with an in-memory store; the abstraction is set up so a real persistence layer can slot in without controller changes.

---

## Endpoints

| Method | Path | Body | Response | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/drafts` | `CreateDraftDto` | `201 { data: DraftPayload }` | `title` defaults to `"Untitled Draft"`; `language` defaults to `en` |
| `GET` | `/v1/drafts/:id` | — | `200 { data: DraftPayload }` | 404 → `DRAFT_NOT_FOUND` |
| `PATCH` | `/v1/drafts/:id` | `UpdateDraftDto` | `200 { data: DraftPayload }` | At least one of `title`, `content`, `language`, `sections` is required |
| `DELETE` | `/v1/drafts/:id` | — | `204 No Content` | 404 → `DRAFT_NOT_FOUND` |

`:id` is validated as a UUID v4 via `ParseUUIDPipe`. Invalid UUIDs fail before they reach the service.

---

## Payload shape

```ts
interface DraftPayload {
  id: string;          // UUID v4
  title: string;       // defaults to "Untitled Draft" when omitted
  content: string;
  language: 'en' | 'es';
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}
```

`created_at` is set once on creation and never updated. `updated_at` is bumped on every successful `PATCH`, including a language-only change.

---

## Key decisions

### In-memory store as the current default

`DraftsService` keeps everything in a `Map<string, Draft>` inside the singleton service instance. The reasoning is the same as for the rhyme index: the simplest implementation that lets the rest of the system be built and tested. Nothing in the public surface assumes the store is in-memory; `DraftsService` exposes `create / findById / update / remove` and nothing else.

The tradeoff is obvious: restarting the gateway loses every draft. This is acceptable while the product is single-user and pre-production. Swapping to SQLite or Postgres replaces the `Map` and the four method bodies; the controller, DTOs, presenter, and exception filter do not change.

### Default title applied at the service, not the controller

`create()` checks `input.title?.length` and falls back to `DEFAULT_TITLE`. Centralizing the default at the service means a future caller (e.g., a batch import) can't accidentally create blank-titled drafts. The DTO accepts an optional title; the service is the single source of the fallback rule.

### PATCH requires at least one mutating field

The controller throws `BadRequestException` if all four of `title`, `content`, `language`, and `sections` are `undefined`. Without this guard, a no-op PATCH would still bump `updated_at`, breaking the contract that `updated_at` reflects an actual change. The check sits in the controller because it is request-shape validation, not domain logic.

### Language defaulting at create, not at read

`create()` defaults `language` to `DEFAULT_LANGUAGE` when omitted. `update()` only touches `language` when explicitly provided. Reads always return the stored value. This avoids silently coercing legacy data on read, which matters once the store is real and predates a future enum expansion.

### Delete is idempotent at the client level

The endpoint returns `404` for unknown IDs, but the web client's `deleteDraft` treats 404 as success: the user asked for the draft to be gone, and it is gone. This keeps "delete twice in a row" from surfacing a spurious error if a request is retried after a network blip.

### Presenter owns the wire shape

[`DraftPresenter`](../src/drafts/presenters/draft.presenter.ts) maps internal `Draft` (camelCase) to `DraftPayload` (snake_case `created_at`/`updated_at`) before sending. This keeps the internal model free to evolve and gives the client a stable, snake_case envelope consistent with the rest of the gateway's responses.

---

## Error contract

| Code | When | HTTP |
| --- | --- | --- |
| `VALIDATION_FAILED` | DTO validation failed (e.g., unsupported language) | 400 |
| `DRAFT_NOT_FOUND` | `GET`, `PATCH`, or `DELETE` for an unknown id | 404 |

Errors come back wrapped in the standard envelope:

```json
{ "error": { "code": "DRAFT_NOT_FOUND", "message": "Draft <id> not found" } }
```

---

## Current limitations

**No persistence across restarts.** See the in-memory decision above.

**No pagination, no listing endpoint.** The current UI only loads drafts from a local "recent drafts" index in the browser. Once the workspace grows beyond a handful of drafts per user, a `GET /v1/drafts` endpoint with pagination becomes table-stakes.

**No concurrent-update protection.** Two clients editing the same draft will last-writer-wins. The current scope is single-user; conflict resolution is a future concern.

**No soft delete.** `remove()` is a hard delete. There is no undo path on the server side. The client's optimistic-delete UX is the only undo affordance, and it disappears as soon as the page reloads.

**No ownership / authorization.** Anyone with a draft's UUID can read, edit, or delete it. Acceptable for single-user local dev; must be addressed before any multi-user deployment.

---

## Areas for improvement

**Persist to SQLite or Postgres.** Replace the `Map` in `DraftsService` with a repository call. The interface is already correct; only the four method bodies and the constructor change.

**Add `GET /v1/drafts` with pagination.** Cursor-based pagination keyed on `updated_at` is the obvious fit once persistence lands.

**Add a `language_changed_at` audit field.** Once drafts are real, knowing when a draft was switched between languages would help in user support and migration audits.

**Soft delete + undo window.** Move `remove()` to a flag-and-timestamp soft delete with a periodic hard-delete job. Pairs naturally with an undo toast on the client.

**Optimistic-concurrency token.** Return an `etag` (e.g., the `updated_at` value) and require it on PATCH. Cheap insurance against accidental overwrites once two clients can talk to the same draft.
