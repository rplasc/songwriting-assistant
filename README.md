# Songwriting Assistant

A focused lyric-writing workspace that counts syllables and finds rhymes as you type — no buttons, no forms, just write.

## The idea

Most rhyme and syllable tools ask you to submit a word or line explicitly. This one watches the line you're currently writing and surfaces feedback automatically, so the analysis sits quietly in the margin while the writing stays front and center.

## How it works

```
Browser (Next.js)  →  Gateway (NestJS)  →  NLP Service (FastAPI / CMU Dict)
```

- You type a lyric line into the editor
- After a short debounce (~150 ms), the active line is sent to the NestJS gateway over WebSocket
- The gateway calls the FastAPI NLP service, which uses the CMU Pronouncing Dictionary
- Syllable counts and rhyme suggestions stream back to the UI in real time

## Current features (Phase 1)

- **Live syllable count** — total for the active line, broken down per word
- **Rhyme suggestions** — perfect, near, and family rhymes for the last word on the active line, with syllable counts
- **Real-time WebSocket transport** — analysis updates as you write, with HTTP fallback available
- **Stale-response protection** — only the result for the line you're currently on is shown
- **Error resilience** — transport failures surface a quiet status message without breaking the editor
- **Responsive layout** — editor and analysis panels sit side by side on desktop, stack on mobile

## Planned (future phases)

- **Multi-document project management** — save and organize drafts by song and section
- **Collaborative presence** — real-time co-writing with another person in the same document
- **Persistent drafts** — auto-save with version history
- **Rhyme scheme tracking** — highlight end-words by rhyme family across the full lyric sheet
- **Meter and stress patterns** — visualize where stresses fall against a chosen meter
- **Account and auth** — personal workspace with login

## Running locally

You need three services. Start them in order.

### 1. NLP service (Python / FastAPI)

```bash
cd apps/nlp-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1       # Windows
# source .venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Gateway (Node.js / NestJS)

```bash
cd apps/gateway
npm install
cp .env.example .env               # set FASTAPI_BASE_URL=http://localhost:8000
npm run start:dev                  # listens on :3000
```

### 3. Web client (Next.js)

```bash
cd apps/web
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
npm run dev                        # listens on :3001
```

Open `http://localhost:3001` and start writing.

## Stack

| Layer | Technology |
|---|---|
| Editor UI | Next.js 16, React 19, TipTap, Tailwind v4 |
| Gateway | NestJS, Socket.IO |
| NLP engine | FastAPI, CMU Pronouncing Dictionary |
| Font | IBM Plex Sans |
| Tests | Vitest, React Testing Library |
