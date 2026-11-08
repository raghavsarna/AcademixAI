# AcademixAI

[![CI](https://github.com/raghavsarna/AcademixAI/actions/workflows/ci.yml/badge.svg)](https://github.com/raghavsarna/AcademixAI/actions/workflows/ci.yml)

AcademixAI makes research papers easier to read. It publishes a daily AI digest from new arXiv papers, turns any uploaded PDF into a plain-language summary, and lets you ask questions about a paper in a chat.

> The backend has been rebuilt; a new web frontend is next. The current pages are served by the backend.

## Features

- **Daily digest:** fetches the newest AI papers from arXiv and writes an accessible newsletter about the most interesting ones.
- **Upload a paper:** extracts the text of a PDF and produces a title, authors, DOI, summary, key findings and methodology. The same paper is never analysed twice: re-uploads are matched by file hash or DOI.
- **Chat:** ask questions about a digest or a paper.

## Stack

| Layer | Tools |
| --- | --- |
| API | FastAPI, Pydantic, JWT auth (PyJWT + bcrypt) |
| Data | SQLAlchemy 2, Alembic migrations, SQLite locally or PostgreSQL |
| AI | Google Gemini via `google-genai` (Gemini 3.1 Flash-Lite, with free Gemma 4 as a rate-limit fallback) |
| PDFs | PyMuPDF |
| Quality | pytest (SQLite and Postgres), ruff, GitHub Actions |

## Run it locally

You need Python 3.12 or newer.

```bash
git clone https://github.com/raghavsarna/AcademixAI.git
cd AcademixAI
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then add GEMINI_API_KEY and SECRET_KEY
```

- `GEMINI_API_KEY`: get one at https://aistudio.google.com/apikey
- `SECRET_KEY`: generate one with `python -c "import secrets; print(secrets.token_hex(32))"`

Create the database, load sample data, and start the server:

```bash
python -m scripts.seed
uvicorn app.main:app --reload
```

Open http://localhost:8000. Interactive API docs are at http://localhost:8000/docs.

To use PostgreSQL instead of SQLite, set `DATABASE_URL=postgresql://user:password@host:5432/academixai` in `.env` and run `python -m scripts.seed` again.

## Generate today's digest

```bash
python -m scripts.generate_digest
```

## Tests and linting

```bash
pytest
ruff check app scripts tests migrations/env.py
ruff format --check app scripts tests migrations/env.py
```

Tests use a temporary SQLite database and a fake model, so they need no API key. To run them against Postgres, set `TEST_DATABASE_URL`. CI runs the suite on both.

## API

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | | Create an account |
| POST | `/api/auth/token` | | Log in with username or email (OAuth2 password form) |
| GET | `/api/auth/me` | ✓ | Current user |
| GET | `/api/digests` | | List digests, newest first (`limit`, `offset`) |
| GET | `/api/digests/{id}` | | A digest with its full content |
| POST | `/api/digests/{id}/chat` | ✓ | Ask about a digest |
| GET | `/api/papers` | ✓ | Your uploaded papers |
| POST | `/api/papers` | ✓ | Upload a PDF (multipart `file`) |
| GET | `/api/papers/{id}` | | A paper's analysis (anyone with the link) |
| POST | `/api/papers/{id}/chat` | ✓ | Ask about a paper |
| GET | `/api/health` | | Health check |

Chat and uploads are rate limited per user; login and sign-up are rate limited per IP address.

## Project layout

```
app/
  main.py          FastAPI app, error handling, static files
  config.py        Settings from environment / .env
  db.py, models.py Database engine and models
  schemas.py       API request/response models
  security.py      Password hashing, tokens, current user
  rate_limit.py    Sliding-window rate limiter
  llm.py           The single wrapper around Gemini
  storage.py       Where uploaded PDFs are kept
  routers/         auth, digests, papers, pages
  services/        papers (PDF → analysis), pdf, chat, digests, markdown
migrations/        Alembic migrations
scripts/           migrate, seed, generate_digest
templates/, static/, images/   Current server-rendered pages
tests/             pytest suite
```
