# Songwriting Assistant

A bilingual lyric-writing workspace that counts syllables and finds rhymes as you type, in English or Spanish.

## The idea

Most rhyme and syllable tools ask you to submit a word or line explicitly. This one watches the line you're currently writing and surfaces feedback automatically, so the analysis sits quietly in the margin while the writing stays front and center. The tool supports both English and Spanish which can be switched between seamlessly.

## How it works

```text
Browser (Next.js)  →  Gateway (NestJS)  →  NLP Service (FastAPI)
                                              ├─ English: CMU Pronouncing Dictionary
                                              └─ Spanish: rule-based phonology + corpus
```

- You type a lyric line into the editor
- After a short debounce (~150 ms), the active line is sent to the NestJS gateway over WebSocket along with the draft's language
- The gateway forwards to the FastAPI NLP service, which routes to the English or Spanish pipeline based on the request
- Syllable counts and rhyme suggestions stream back to the UI in real time
- Drafts are persisted through the gateway's REST API and restored on reload, language and all

## Current features

### Writing & analysis

- **Live syllable count** — total for the active line, broken down per word, with italicized estimates for words missing from the dictionary
- **Rhyme suggestions** — perfect/near for English, consonant/asonante for Spanish, ranked and labeled in the local vocabulary
- **Rhyme-mode toggle** — switch between strict and loose matching from the editor header
- **Real-time WebSocket transport** — analysis updates as you write, with HTTP fallback available
- **Stale-response protection** — only the result for the line you're currently on is shown
- **Error resilience** — transport failures surface a quiet status message without breaking the editor

### Bilingual support (Current Phase)

- **Per-draft language** — choose English or Español from the editor header; the choice persists with the draft
- **Language-aware analysis** — Spanish lines route through Spanish phonology and rhyme rules; English keeps its CMU-based pipeline untouched
- **Localized empty states and copy** — the UI speaks in the language you're writing in
- **Honest tonal split** — Phase 3 deliberately scopes to single-language drafts; mixed-language line detection is out of scope for this phase

### Drafts

- **Auto-save** - debounced server-side persistence; status shown in the header
- **Recent drafts menu** - load, switch between, and delete saved drafts
- **Manual save** and **offline retry** for when the gateway is unreachable

### Layout

- **Responsive** - editor and analysis panels sit side by side on desktop, stack on mobile
- **Reduced-motion aware** - transitions collapse when the user opts out

## Planned (future phases)

- **Mixed-language intelligence** - line-by-line language detection for code-switched lyrics
- **Rhyme scheme tracking** - highlight end-words by rhyme family across the full lyric sheet
- **Meter and stress patterns** - visualize where stresses fall against a chosen meter
- **Multi-document project management** - organize drafts by song and section
- **Collaborative presence** - real-time co-writing with another person in the same document
- **Version history** - restore prior states of a draft
- **Account and auth** - personal workspace with login
- **Mobile App** - write lyrics locally through a native app

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

Open `http://localhost:3001` and start writing. Use the **English · Español** toggle in the header to switch languages.

## Stack

| Layer | Technology |
|---|---|
| Editor UI | Next.js 16, React 19, TipTap, Tailwind v4 |
| Gateway | NestJS, Socket.IO |
| NLP engine | FastAPI; CMU Pronouncing Dictionary (English) + rule-based phonology and corpus (Spanish) |
| Font | IBM Plex Sans |
| Tests | Vitest + React Testing Library (web), Jest (gateway), Pytest (NLP) |
