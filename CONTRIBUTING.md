# Contributing

Thanks for helping improve Songwriting Assistant. This project has three main
apps: a Next.js web client, a NestJS gateway, and a FastAPI NLP service. Keep
changes focused and tested so the next contributor can follow them.

## Getting Started

1. Fork or clone the repository.
2. Create a working branch from the latest main branch.
3. Install dependencies for the app or service you are changing.
4. Make your changes with focused commits.
5. Run the relevant tests and checks before opening a pull request.

See [README.md](README.md) for full local setup instructions.

## Branch Naming

Branch names should start with either `feature` or `bugfix`, followed by your
username or initials, then the issue number or a short description of the work.

Use this format:

```text
feature/<username-or-initials>/<issue-or-description>
bugfix/<username-or-initials>/<issue-or-description>
```

Examples:

```text
feature/rp/focus-mode
bugfix/rplasc/issue-23
```

Use `feature` for new behavior or planned enhancements. Use `bugfix` for
defects, regressions, and other small fixes.

## Local Development

Run only the services needed for your change, or start all three when testing
end-to-end behavior.

```powershell
# NLP service
cd apps/nlp-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Gateway
cd apps/gateway
npm install
npm run start:dev

# Web client
cd apps/web
npm install
npm run dev
```

The web client runs on `http://localhost:3001`, the gateway on
`http://localhost:3000`, and the NLP service on `http://localhost:8000`.

## Testing

Run the checks for the area you changed.

```powershell
# Web client
cd apps/web
npm run lint
npm run test

# Gateway
cd apps/gateway
npm run lint
npm run test

# NLP service
cd apps/nlp-service
pytest
```

If a check cannot be run locally, mention that in your pull request and explain
why.

## Pull Requests

Before opening a pull request:

- Rebase or merge the latest main branch into your branch.
- Keep the PR focused on one feature, fix, or cleanup.
- Include a clear summary of what changed and why.
- Link the related issue when one exists.
- Add or update tests for behavior changes.
- Include screenshots or short notes for UI changes.
- Call out any known limitations, follow-up work, or setup needed to review.

## Code Guidelines

- Follow the style already used in the app or service you are editing.
- Prefer small, readable functions over broad rewrites.
- Keep API contracts explicit and update callers together.
- Avoid unrelated formatting or refactoring in feature and bugfix PRs.
- Keep user-facing copy consistent in tone with the rest of the app.

## Documentation

Update documentation whenever a change affects setup, environment variables,
API behavior, developer workflows, or what users see. Check the root
[README.md](README.md), app-specific README files, and docs inside
`apps/nlp-service/docs`.
