# NLP Service — FastAPI Rhyme & Analysis Engine

Bilingual (English + Spanish) NLP microservice for the songwriting assistant.
Provides rhyme suggestions, syllable analysis, and draft-level structural
analysis. English is backed by the CMU Pronouncing Dictionary; Spanish uses a
rule-based G2P pipeline with a synthesized frequency corpus.

## Run locally

```powershell
# from apps/nlp-service
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Endpoints

| Method | Route | Description |
| --- | --- | --- |
| GET | `/healthz` | Health check |
| POST | `/v1/rhymes` | Rhyme suggestions for a word |
| POST | `/v1/analyze-line` | Syllable analysis for a single line, plus same-line `inner_rhymes` groups |
| POST | `/v1/analyze-draft` | Structural analysis for a full draft, plus draft-wide `inner_rhymes` groups |
| POST | `/v1/analyze-draft-compare` | Delta analysis between two draft versions |

```powershell
# Health
curl http://localhost:8000/healthz

# Rhymes — English perfect rhymes (default)
curl -X POST http://localhost:8000/v1/rhymes `
  -H "Content-Type: application/json" `
  -d '{"word":"fire","limit":10,"language":"en","mode":"perfect"}'

# Rhymes — Spanish assonant rhymes
curl -X POST http://localhost:8000/v1/rhymes `
  -H "Content-Type: application/json" `
  -d '{"word":"canción","limit":10,"language":"es","mode":"assonant"}'

# Line analysis
curl -X POST http://localhost:8000/v1/analyze-line `
  -H "Content-Type: application/json" `
  -d '{"line":"I see the fire in your eyes","language":"en"}'

# Draft analysis
curl -X POST http://localhost:8000/v1/analyze-draft `
  -H "Content-Type: application/json" `
  -d '{"language":"en","content":"Line one here\nLine two here\nLine three\nLine four"}'

# Draft compare
curl -X POST http://localhost:8000/v1/analyze-draft-compare `
  -H "Content-Type: application/json" `
  -d '{"language":"en","previous":{"content":"Line one\nLine two"},"current":{"content":"Line one\nLine three"}}'
```

### Supported modes

| Language | `mode` values | Default |
| --- | --- | --- |
| `en` | `perfect`, `near` | `perfect` |
| `es` | `consonant`, `assonant` | `consonant` |

## Redis response cache

`/v1/analyze-draft` and `/v1/analyze-draft-compare` support an opt-in Redis
cache that turns repeat analyses of the same content into near-instant lookups.
The cache is **off by default** so local dev and CI don't require Redis.

| Variable | Default | Description |
| --- | --- | --- |
| `NLP_CACHE_ENABLED` | `false` | Set to `true` to activate |
| `NLP_CACHE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `NLP_CACHE_TTL_SECONDS` | `3600` | Entry lifetime in seconds (1 hour) |
| `NLP_CACHE_KEY_PREFIX` | `nlp:v1` | Prefix for all cache keys; bump to invalidate |

Cache keys are content-addressed (`sha256` of the canonical JSON payload), so
any payload change automatically results in a cache miss. If Redis is
unreachable the service logs a warning and computes a fresh response. The cache
is purely a performance optimisation and never a hard dependency.

```powershell
# Enable cache for a local dev session (requires Redis on localhost:6379)
$env:NLP_CACHE_ENABLED = "true"
uvicorn app.main:app --reload --port 8000
```

## Tests

```powershell
pytest
```

## Docker

```powershell
docker build -t nlp-service .
docker run --rm -p 8000:8000 nlp-service

# With Redis cache enabled
docker run --rm -p 8000:8000 `
  -e NLP_CACHE_ENABLED=true `
  -e NLP_CACHE_REDIS_URL=redis://host.docker.internal:6379/0 `
  nlp-service
```

## Further reading

- [`docs/service-overview.md`](docs/service-overview.md) — design decisions and tradeoffs
- [`docs/draft-analysis.md`](docs/draft-analysis.md) — draft analysis feature design
- [`docs/bilingual.md`](docs/bilingual.md) — cross-language architectural contract, including per-feature capability levels
- [`docs/language-routing.md`](docs/language-routing.md) — request routing
- [`docs/spanish-pipeline.md`](docs/spanish-pipeline.md) — Spanish-specific implementation
- [`docs/taxonomy.md`](docs/taxonomy.md) — Rhyme taxonomy and phrase-ending rules
- [`docs/draft_intelligence.md`](docs/draft_intelligence.md) — threshold reference: clustering, motifs, contrast, consistency hints
- [`docs/inner-rhyme-detection.md`](docs/inner-rhyme-detection.md) — word-level rhyme grouping (`inner_rhymes`) for `/v1/analyze-line` and `/v1/analyze-draft`
