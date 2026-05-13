# Gateway Overview

Transport and orchestration layer between the editor UI and the FastAPI rhyme/syllable engine. Accepts HTTP and WebSocket requests from the editor, composes downstream calls to FastAPI, and returns a UI-friendly combined payload.

---

## Architecture

```text
Editor UI
   │
   ├── HTTP  POST /v1/editor/analyze
   └── WS    /editor  editor.analyze
              │
           EditorService
              │
      ┌───────┴────────┐
      │                │
 POST /v1/analyze-line  POST /v1/rhymes
      │                │
      └──── FastAPI NLP service ────┘
```

Both the HTTP controller and the WebSocket gateway share a single `EditorService` so orchestration logic is defined once and tested once.

---

## Key decisions

### HTTP-only transport to FastAPI

FastAPI is called over plain HTTP using `@nestjs/axios`. The alternatives were gRPC (lower overhead, typed contracts via protobuf) and a message queue (decoupled, buffered). HTTP was chosen because it is the easiest to debug locally, requires no additional infrastructure, and the existing FastAPI service already exposes a REST interface. For Phase 1, the latency profile is dominated by FastAPI's NLP processing time rather than transport overhead, so HTTP is the right default.

### Shared orchestration service

The HTTP controller and WebSocket gateway both delegate to `EditorService.analyze()`. This means the response contract is identical regardless of how the client connects, and orchestration bugs only need to be fixed in one place. The tradeoff is that any behavior that should differ between transports (e.g., per-connection caching) would require injecting context from the calling layer rather than being handled transparently in the service.

### Presenter layer for response shaping

A dedicated `EditorResponsePresenter` translates FastAPI's internal field names (`total_syllables`, `rhyme_type`) into the stable UI contract (`syllables.total`, `type`). This insulates the frontend from FastAPI implementation details and means FastAPI's schema can evolve without breaking the client. The cost is an extra mapping step and a second set of types to keep synchronized with the FastAPI schemas.

### Socket.IO over raw ws

The WebSocket gateway uses Socket.IO via `@nestjs/platform-socket.io`. Socket.IO provides named events, namespaces, and automatic reconnection, which map directly to the `editor.analyze` / `editor.analysis` / `editor.error` event model in the spec. Raw `ws` would have required a hand-rolled message envelope. The tradeoff is that Socket.IO clients must be used on the frontend; plain `WebSocket` browser clients are not compatible without the Socket.IO polling fallback.

### Client-side debouncing

Debouncing is left to the editor UI. The gateway applies no server-side throttle or debounce. This keeps the gateway stateless and simple. The risk is that a misbehaving client could generate excessive calls to FastAPI; a defensive throttle at the gateway level is a reasonable Phase 2 addition if logs show it is needed.

### Env validation at startup

Joi validates all required environment variables when the app starts. A missing `FASTAPI_BASE_URL` causes an immediate crash with a clear message rather than a confusing runtime error on the first request. The cost is that running the app without a `.env` file requires all required vars to be set in the environment explicitly.

### Global exception filter with error codes

All errors — validation failures, downstream unavailability, and internal errors — are shaped into a single `{ error: { code, message } }` envelope before reaching the client. Codes are stable strings (`VALIDATION_FAILED`, `FASTAPI_UNAVAILABLE`, `UPSTREAM_FAILED`) that the frontend can branch on without parsing human-readable messages. The filter deliberately strips internal stack traces and upstream error bodies from client-facing responses.

---

## Current limitations

**No server-side debounce or rate limiting.** Every `editor.analyze` event results in one or two FastAPI calls. A fast typist or a looping client can saturate the NLP service. The mitigation is to enforce debouncing on the client side before connecting.

**No connection-level state.** Each request is fully self-contained. There is no concept of an editing session, song context, or per-user history. The presenter cannot apply cross-line heuristics (e.g., rhyme scheme awareness) because it only sees a single line per request.

**Sequential downstream calls.** Line analysis and rhyme lookup are called in series. The rhyme call can only start after line analysis returns the last word. For most lines this adds one round-trip of latency on top of the analysis time.

**Error codes are flat.** The `UPSTREAM_FAILED` code covers all non-reachability FastAPI errors (4xx and 5xx). Clients cannot distinguish between a bad request sent to FastAPI and a FastAPI internal error without inspecting the HTTP status code alongside the code string.

**No request tracing across services.** The gateway generates a `request_id` and logs it, but does not forward it to FastAPI (e.g., as an `x-request-id` header). Correlating a slow gateway log entry with the corresponding FastAPI log entry requires timestamp matching.

**WebSocket CORS origin is read from process.env at module load time.** The `@WebSocketGateway` decorator evaluates `process.env.CORS_ORIGIN` when the class is defined, not when the app is configured. This means the gateway does not pick up the typed config value from `ConfigService` at startup.

**No authentication or authorization.** There is no token validation, session check, or API key enforcement. This is acceptable for local development but must be addressed before the gateway is exposed to any non-local network.

---

## Areas for improvement

**Forward `x-request-id` to FastAPI.** Passing the gateway request ID to FastAPI as a header would allow end-to-end trace correlation across both services using only log search, without a distributed tracing system.

**Parallel downstream calls where possible.** If the last word of a line is known from a previous request or can be extracted before full analysis completes, the rhyme call could be issued concurrently with or ahead of the full line analysis. Even without that optimization, a future `analyze-and-rhyme` endpoint on FastAPI could collapse both calls into one round-trip.

**Server-side throttle per connection.** A lightweight per-socket throttle (e.g., maximum N events per second) would protect FastAPI from burst traffic without requiring the UI to be well-behaved. `@nestjs/throttler` has WebSocket support.

**Richer error codes.** Distinguishing `FASTAPI_BAD_REQUEST` (the gateway sent invalid data) from `FASTAPI_INTERNAL_ERROR` (FastAPI failed on valid data) would let the client display more useful diagnostics in development mode.

**Fix WebSocket CORS to use ConfigService.** Replace the `process.env.CORS_ORIGIN` read in `@WebSocketGateway` with a dynamic adapter configuration so CORS origin follows the same config path as the rest of the app.

**Session context for rhyme scheme awareness.** Passing a song-level context (recent line endings, selected rhyme scheme) alongside each line analysis request would let FastAPI rank rhyme candidates relative to the active song rather than treating every line in isolation.

**Structured logging.** The current logging interceptor emits a plain string. Switching to structured JSON logs (e.g., via `nestjs-pino`) would make log lines machine-parseable and easier to route to a log aggregator.
