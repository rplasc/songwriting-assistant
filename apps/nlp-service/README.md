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
| POST | `/v1/analyze-line` | Syllable analysis for a single line |
| POST | `/v1/analyze-draft` | Structural analysis for a full draft |

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
```

### Supported modes

| Language | `mode` values | Default |
| --- | --- | --- |
| `en` | `perfect`, `near` | `perfect` |
| `es` | `consonant`, `assonant` | `consonant` |

## Tests

```powershell
pytest
```

## Docker

```powershell
docker build -t nlp-service .
docker run --rm -p 8000:8000 nlp-service
```

## Further reading

- [`docs/service-overview.md`](docs/service-overview.md) — design decisions and tradeoffs
- [`docs/draft-analysis.md`](docs/draft-analysis.md) — draft analysis feature design
- [`docs/bilingual.md`](docs/bilingual.md) — cross-language architectural contract
- [`docs/language-routing.md`](docs/language-routing.md) — request routing
- [`docs/spanish-pipeline.md`](docs/spanish-pipeline.md) — Spanish-specific implementation
