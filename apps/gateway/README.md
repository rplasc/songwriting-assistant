# Songwriting Gateway (NestJS)

Thin orchestration layer between the editor UI and the FastAPI rhyme/syllable
engine in `apps/nlp-service`. Validates editor payloads, calls FastAPI over
internal HTTP, and reshapes the response into a UI-friendly contract over
both HTTP and WebSocket.

See [`nestjs_phase1_implementation_plan.md`](./nestjs_phase1_implementation_plan.md)
for the full spec.

## Prerequisites

- Node.js 20+
- FastAPI service running locally — see `apps/nlp-service/README.md`.

## Setup

```bash
npm install
cp .env.example .env   # then edit as needed
```

### Environment variables

| Variable             | Default                 | Description                              |
| -------------------- | ----------------------- | ---------------------------------------- |
| `PORT`               | `3000`                  | Gateway HTTP/WS port                     |
| `NODE_ENV`           | `development`           | `development` \| `production` \| `test`  |
| `FASTAPI_BASE_URL`   | _(required)_            | Base URL of the FastAPI NLP service      |
| `FASTAPI_TIMEOUT_MS` | `5000`                  | Per-request timeout when calling FastAPI |
| `CORS_ORIGIN`        | `*`                     | Allowed origin for the editor UI         |

## Run

```bash
npm run start:dev   # watch mode
npm run start       # one-shot
npm run start:prod  # from compiled dist/
```

Startup logs the resolved FastAPI URL.

## HTTP surface

```text
GET  /health                    -> { status: "ok", service: "nestjs-api" }
GET  /health/dependencies       -> { status, fastapi: { reachable } }   (always 200)
POST /v1/editor/analyze         -> combined syllable + rhyme payload
```

Example:

```bash
curl -X POST http://localhost:3000/v1/editor/analyze \
  -H 'Content-Type: application/json' \
  -d '{"line":"I see the fire in your eyes"}'
```

Error envelope (all error responses):

```json
{ "error": { "code": "VALIDATION_FAILED", "message": "line should not be empty" } }
```

Known codes: `VALIDATION_FAILED`, `FASTAPI_UNAVAILABLE`, `UPSTREAM_FAILED`,
`NOT_FOUND`, `INTERNAL_ERROR`.

## WebSocket surface

Socket.IO namespace `/editor`.

- Client → server: `editor.analyze` with `{ line: string }`
- Server → client: `editor.analysis` with the same payload shape as HTTP
- Server → client: `editor.error` with `{ message, code }`

```js
import { io } from 'socket.io-client';
const s = io('http://localhost:3000/editor');
s.on('editor.analysis', console.log);
s.on('editor.error', console.error);
s.emit('editor.analyze', { line: 'Broken dreams in neon light' });
```

## Tests

```bash
npm test            # unit
npm run test:e2e    # HTTP + WebSocket e2e (FastAPI is mocked)
npm run test:cov    # coverage
```

## Architecture notes

- **No language logic in this service.** Syllable counting, rhyme ranking, and
  phoneme handling live in `apps/nlp-service`. The gateway is transport,
  validation, and presentation only.
- The `FastapiClient` is the only thing that knows FastAPI URLs and shapes.
- `EditorService` is shared by both the HTTP controller and the WebSocket
  gateway so behavior stays consistent.
- Request IDs are propagated via the `x-request-id` header (generated if
  absent) and echoed in logs and editor response `meta`.
