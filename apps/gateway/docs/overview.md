# Gateway Overview

Transport and orchestration layer between the editor UI and the FastAPI rhyme/syllable engine. Accepts HTTP and WebSocket requests from the editor, composes downstream calls to FastAPI, persists drafts, and returns UI-friendly combined payloads. Bilingual as of Phase 3 — language is a first-class request and persistence concern.

---

## Architecture

```text
Editor UI
   │
   ├── HTTP  POST   /v1/editor/analyze
   ├── HTTP  POST   /v1/drafts
   ├── HTTP  GET    /v1/drafts/:id
   ├── HTTP  PATCH  /v1/drafts/:id
   ├── HTTP  DELETE /v1/drafts/:id
   └── WS    /editor  editor.analyze
              │
        ┌─────┴──────┐
        │            │
   EditorService  DraftsService
        │            │
   LanguageRequestMapper           (in-memory store, Phase 3)
        │
  POST /v1/analyze-line   POST /v1/rhymes
        │                        │
        └─── FastAPI NLP service ┘
                (routed per language: en | es)
```

Both the HTTP controller and the WebSocket gateway share a single `EditorService` so orchestration logic is defined once and tested once. Drafts live in their own module with their own controller, service, and presenter.

---

## Key decisions

### Language is request-level, not connection-level

Every analyze request carries an explicit `language` field (defaulting to `en`). The gateway does not maintain per-connection language state, so a single client can switch languages between requests without reconnecting and so that the rhyme/analysis pipeline never has to read shared mutable state.

The defaulting and rhyme-mode resolution live in [`LanguageRequestMapper`](../src/editor/mappers/language-request.mapper.ts) so the same defaults apply whether the request arrives via HTTP or WebSocket. See [`bilingual.md`](./bilingual.md) for the full language contract.

### Drafts are owned by the gateway, not FastAPI

The NLP service is stateless. Persistence sits at the gateway because the gateway already owns the request envelope, validation, and the language contract — keeping drafts adjacent to that surface avoids a second validation layer in FastAPI. Phase 3 ships drafts as an in-memory store; the [`drafts.md`](./drafts.md) doc covers the contract and the limitations of the current implementation.

### HTTP-only transport to FastAPI

FastAPI is called over plain HTTP using `@nestjs/axios`. The alternatives were gRPC (lower overhead, typed contracts via protobuf) and a message queue (decoupled, buffered). HTTP was chosen because it is the easiest to debug locally, requires no additional infrastructure, and the existing FastAPI service already exposes a REST interface. Latency profile is still dominated by NLP processing time rather than transport overhead.

### Shared orchestration service

The HTTP controller and WebSocket gateway both delegate to `EditorService.analyze()`. The response contract is identical regardless of how the client connects, and orchestration bugs only need to be fixed in one place. The tradeoff is that any behavior that should differ between transports (e.g., per-connection caching) would require injecting context from the calling layer rather than being handled transparently in the service.

### Presenter layer for response shaping

A dedicated `EditorResponsePresenter` translates FastAPI's internal field names (`total_syllables`, `rhyme_type`) into the stable UI contract (`syllables.total`, `type`), and echoes the resolved `language` and `mode` back to the client so the editor doesn't have to remember what it asked for. This insulates the frontend from FastAPI implementation details and means FastAPI's schema can evolve without breaking the client.

### Socket.IO over raw ws

The WebSocket gateway uses Socket.IO via `@nestjs/platform-socket.io`. Socket.IO provides named events, namespaces, and automatic reconnection, which map directly to the `editor.analyze` / `editor.analysis` / `editor.error` event model. Raw `ws` would have required a hand-rolled message envelope. The tradeoff is that Socket.IO clients must be used on the frontend; plain `WebSocket` browser clients are not compatible without the polling fallback.

### Client-side debouncing

Debouncing is left to the editor UI. The gateway applies no server-side throttle or debounce. This keeps the gateway stateless and simple. The risk is that a misbehaving client could generate excessive calls to FastAPI; a defensive throttle at the gateway level remains a reasonable future addition if logs show it is needed.

### Env validation at startup

Joi validates all required environment variables when the app starts. A missing `FASTAPI_BASE_URL` causes an immediate crash with a clear message rather than a confusing runtime error on the first request.

### Global exception filter with error codes

All errors — validation failures, downstream unavailability, internal errors, and 404s from `DraftsService` — are shaped into a single `{ error: { code, message } }` envelope before reaching the client. Codes are stable strings (`VALIDATION_FAILED`, `FASTAPI_UNAVAILABLE`, `UPSTREAM_FAILED`, `DRAFT_NOT_FOUND`) that the frontend can branch on without parsing human-readable messages. The filter deliberately strips internal stack traces and upstream error bodies from client-facing responses.

---

## Module map

| Module | Responsibility | Detailed doc |
| --- | --- | --- |
| `editor/` | Analyze-line orchestration (HTTP + WS), language defaulting, response shaping | inline in this file |
| `drafts/` | CRUD over drafts, in-memory store, language-aware payloads | [`drafts.md`](./drafts.md) |
| `fastapi/` | Typed HTTP client + DTOs for the NLP service | inline |
| `common/` | Shared filters, interceptors, enums (language, rhyme mode) | inline |
| `config/` | Joi-validated environment config | inline |
| `health/` | Liveness check | inline |

For the language-contract specifics (enum, defaults, mode-per-language resolution, validation behavior), see [`bilingual.md`](./bilingual.md).

---

## Current limitations

**No server-side debounce or rate limiting.** Every `editor.analyze` event results in one or two FastAPI calls. A fast typist or a looping client can saturate the NLP service. The mitigation is to enforce debouncing on the client side before connecting.

**Drafts are in-memory and process-local.** Restarting the gateway loses every saved draft. Acceptable for the current Phase 3 scope (single developer, single user) but the obvious next step before any non-local deployment. See [`drafts.md`](./drafts.md) for the swap-in points.

**No connection-level state.** Each request is fully self-contained. There is no concept of an editing session, song context, or per-user history. The presenter cannot apply cross-line heuristics (e.g., rhyme scheme awareness) because it only sees a single line per request.

**Sequential downstream calls.** Line analysis and rhyme lookup are called in series. The rhyme call can only start after line analysis returns the last word.

**Error codes are flat.** `UPSTREAM_FAILED` covers all non-reachability FastAPI errors (4xx and 5xx). Clients cannot distinguish between a bad request sent to FastAPI and a FastAPI internal error without inspecting the HTTP status code alongside the code string.

**No request tracing across services.** The gateway generates a `request_id` and logs it, but does not forward it to FastAPI (e.g., as an `x-request-id` header).

**WebSocket CORS origin is read from `process.env` at module load time.** The `@WebSocketGateway` decorator evaluates `process.env.CORS_ORIGIN` when the class is defined, not when the app is configured. The gateway does not pick up the typed config value from `ConfigService` at startup.

**No authentication or authorization.** Acceptable for local development; must be addressed before any non-local exposure.

---

## Areas for improvement

**Persist drafts to a real store.** SQLite or Postgres behind the existing `DraftsService` interface — `DraftsService` already owns the abstraction so the controller does not need to change.

**Forward `x-request-id` to FastAPI.** End-to-end trace correlation across both services using only log search, without a distributed tracing system.

**Parallel downstream calls where possible.** A future `analyze-and-rhyme` endpoint on FastAPI could collapse both calls into one round-trip; alternatively the gateway could extract the last word locally and issue both requests concurrently.

**Server-side throttle per connection.** A lightweight per-socket throttle (e.g., maximum N events per second) would protect FastAPI from burst traffic without requiring the UI to be well-behaved. `@nestjs/throttler` has WebSocket support.

**Richer error codes.** Distinguishing `FASTAPI_BAD_REQUEST` (the gateway sent invalid data) from `FASTAPI_INTERNAL_ERROR` (FastAPI failed on valid data) would let the client display more useful diagnostics in development mode.

**Fix WebSocket CORS to use ConfigService.** Replace the `process.env.CORS_ORIGIN` read in `@WebSocketGateway` with a dynamic adapter configuration so CORS origin follows the same config path as the rest of the app.

**Session context for rhyme scheme awareness.** Passing a song-level context (recent line endings, selected rhyme scheme) alongside each line analysis request would let FastAPI rank rhyme candidates relative to the active song rather than treating every line in isolation.

**Structured logging.** Switching to structured JSON logs (e.g., via `nestjs-pino`) would make log lines machine-parseable.
