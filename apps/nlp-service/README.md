# NLP Service — FastAPI Rhyme Engine

Phase 1 language engine that returns English rhyme suggestions and syllable
analysis for the songwriting assistant. Backed by the CMU Pronouncing
Dictionary loaded once at startup.

See [fastapi_rhyme_engine_implementation_plan.md](fastapi_rhyme_engine_implementation_plan.md)
for the full product spec.

## Run locally

```powershell
# from apps/nlp-service
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then:

- `GET  http://localhost:8000/healthz`
- `POST http://localhost:8000/v1/rhymes`        body: `{"word":"fire","limit":10}`
- `POST http://localhost:8000/v1/analyze-line`  body: `{"line":"I see the fire in your eyes"}`

## Tests

```powershell
pytest
```

## Docker

```powershell
docker build -t nlp-service .
docker run --rm -p 8000:8000 nlp-service
```
