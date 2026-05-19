# Language Routing

How a request finds the right engine. Small file, narrow scope — anything broader belongs in [`bilingual.md`](./bilingual.md).

---

## The router

[`LanguageRouter`](../app/services/language_router.py) is a frozen registry of `LanguageContext` instances, keyed by ISO language code. It is constructed once in the FastAPI `lifespan` hook and stored on `app.state.language_router`.

```python
class LanguageRouter:
    def __init__(self, contexts: dict[str, LanguageContext]) -> None: ...
    def get(self, code: str) -> LanguageContext  # raises UnsupportedLanguageError
    @property
    def supported(self) -> tuple[str, ...]
```

A `LanguageContext` bundles the engine, repository, index, and three services for one language. Every per-language object the request path needs is reachable from the context.

---

## The request path

```
1. Route handler reads `language` from the validated request body.
2. router.get(language) → LanguageContext
3. Handler calls ctx.engine.validate_mode(mode) if a mode is present.
4. Handler calls ctx.syllable_service / ctx.rhyme_service with the request data.
5. Presenter wraps the result with language + mode echo in `meta`.
```

No shared code branches on the language code itself. Once `router.get` returns, the handler is operating on a single language's pipeline.

---

## Errors

| Error | Raised by | Wire shape |
| --- | --- | --- |
| `UnsupportedLanguageError` | `LanguageRouter.get` | `{ "error": { "code": "validation_error", "message": "language '<code>' is not supported. Supported languages: en, es" } }` |
| `UnsupportedModeError` | `engine.validate_mode` | `{ "error": { "code": "validation_error", "message": "mode '<mode>' is not supported for language '<code>'. Supported: ..." } }` |

Both errors include the supported set in the message so the client (or a curl user) can fix the request without re-reading the docs.

---

## Why a registry instead of a factory

The router stores fully-built `LanguageContext` instances rather than factories that build a context on demand. Two reasons:

1. **Cold-start fairness.** Every language pays its build cost once at startup. No request is the unlucky one that triggers a 2-second rhyme-index build.
2. **Failure surfaces early.** If a language's repository or index fails to build, the service refuses to start. A factory model would let that failure hide until the first request for that language arrived in production.

The tradeoff is startup time scales linearly with supported languages. Acceptable until the count is large; if it isn't, the registry can be made lazy without changing the request-time contract.

---

## What lives outside the router

- **Default language selection** — the gateway owns this. FastAPI requires an explicit `language` on each request.
- **Mode defaulting** — also the gateway. FastAPI requires an explicit `mode` if the request supplies one at all; it does not apply a per-language default itself. (The engine's `default_mode` exists for code that needs an "any sensible mode" answer, e.g., introspection.)
- **Language coercion / translation** — neither the gateway nor FastAPI does this.

If you need any of the above to live inside FastAPI, the right answer is almost always "the gateway should do it" — keep FastAPI's per-request behavior fully explicit.
