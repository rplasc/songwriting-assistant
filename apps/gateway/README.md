# Songwriting Gateway (NestJS)

Thin orchestration layer between the editor UI and the FastAPI NLP service in
`apps/nlp-service`. Validates payloads, persists song drafts, calls FastAPI
over internal HTTP, and reshapes responses into a stable UI contract over both
HTTP and WebSocket.

## Prerequisites

- Node.js 20+
- FastAPI NLP service running locally — see `apps/nlp-service/README.md`.

## Setup

```bash
npm install
cp .env.example .env   # then edit as needed
```

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `3000` | Gateway HTTP/WS port |
| `NODE_ENV` | `development` | `development` \| `production` \| `test` |
| `FASTAPI_BASE_URL` | _(required)_ | Base URL of the FastAPI NLP service |
| `FASTAPI_TIMEOUT_MS` | `5000` | Per-request timeout when calling FastAPI |
| `CORS_ORIGIN` | `*` | Allowed origin for the editor UI |

## Run

```bash
npm run start:dev   # watch mode
npm run start       # one-shot
npm run start:prod  # from compiled dist/
```

Startup logs the resolved FastAPI URL and timeout.

## HTTP surface

```text
GET  /health                        → { status: "ok", service: "nestjs-api" }
GET  /health/dependencies           → { status, fastapi: { reachable } }  (always 200)

POST /v1/editor/analyze             → combined syllable + rhyme payload
POST /v1/editor/analyze-draft       → structural draft analysis (rhyme scheme, cadence, repetition)

POST   /v1/drafts                   → 201 { data: DraftPayload }
GET    /v1/drafts/:id               → 200 { data: DraftPayload }
PATCH  /v1/drafts/:id               → 200 { data: DraftPayload }
DELETE /v1/drafts/:id               → 204
```

Examples:

```bash
# Per-line analysis — English (default)
curl -X POST http://localhost:3000/v1/editor/analyze \
  -H 'Content-Type: application/json' \
  -d '{"line":"I see the fire in your eyes","language":"en","rhyme_mode":"perfect"}'

# Per-line analysis — Spanish
curl -X POST http://localhost:3000/v1/editor/analyze \
  -H 'Content-Type: application/json' \
  -d '{"line":"Vivo entre sombras","language":"es","rhyme_mode":"consonant"}'

# Draft analysis
curl -X POST http://localhost:3000/v1/editor/analyze-draft \
  -H 'Content-Type: application/json' \
  -d '{"content":"Line one\nLine two\nLine three\nLine four","language":"en"}'

# Create a draft
curl -X POST http://localhost:3000/v1/drafts \
  -H 'Content-Type: application/json' \
  -d '{"content":"First verse here","title":"My Song","language":"en"}'
```

Error envelope (all error responses):

```json
{ "error": { "code": "VALIDATION_FAILED", "message": "line should not be empty" } }
```

| Code | HTTP | Cause |
| --- | --- | --- |
| `VALIDATION_FAILED` | 400 | DTO validation failed |
| `DRAFT_NOT_FOUND` | 404 | Unknown draft ID |
| `CONFLICT` | 409 | If-Match version mismatch on PATCH |
| `FASTAPI_UNAVAILABLE` | 503 | NLP service unreachable |
| `UPSTREAM_FAILED` | 502 | FastAPI returned an unexpected error |
| `INTERNAL_ERROR` | 500 | Unhandled gateway error |

## WebSocket surface

Socket.IO namespace `/editor`.

```text
Client → Server  editor.analyze   { line, language?, rhyme_mode? }
Server → Client  editor.analysis  EditorAnalysisPayload
Server → Client  editor.error     { code, message }
```

```js
import { io } from 'socket.io-client';
const s = io('http://localhost:3000/editor');
s.on('editor.analysis', console.log);
s.on('editor.error', console.error);
s.emit('editor.analyze', {
  line: 'Broken dreams in neon light',
  language: 'en',
  rhyme_mode: 'perfect',
});
```

Supported `language` values: `en`, `es`. `rhyme_mode` defaults to `perfect`
for English and `consonant` for Spanish.

## Tests

```bash
npm test            # unit
npm run test:e2e    # HTTP + WebSocket e2e (FastAPI is mocked)
npm run test:cov    # coverage
```

## Further reading

- [`docs/overview.md`](docs/overview.md) — architecture and design decisions
- [`docs/drafts.md`](docs/drafts.md) — drafts CRUD contract and limitations
- [`docs/bilingual.md`](docs/bilingual.md) — language contract and defaulting rules
