# AcademixAI

[![CI](https://github.com/raghavsarna/AcademixAI/actions/workflows/ci.yml/badge.svg)](https://github.com/raghavsarna/AcademixAI/actions/workflows/ci.yml)

**What changed in AI research today, and every paper explained at your level.**

Hundreds of AI papers land on arXiv every day. AcademixAI reads each day's new papers in AI, machine learning, language and vision, picks the ones that actually move the field, and draws them as a metro map: research areas are coloured lines, the day's papers are new stations, and a paper that spans two areas is an interchange. Open any paper and read it at the depth that suits you: **Plain**, **Student** or **Expert**.

![The landing page: today's edition drawn as a metro map](docs/screenshots/01-home.png)

## What it does

- **A daily changelog, not a newsletter.** Each edition ranks the ~10 papers that change the field most, and says for each one what it claims is new, what kind of change it is, and which earlier work it extends, challenges or replaces.
- **One paper, three readers.** Every paper is explained three times: for someone who has never read a paper, for a student meeting the idea, and for a practitioner who wants the method and the numbers. Switch depth in place; the choice is kept in the link.
- **Explain your own paper.** Upload a PDF and get the same treatment from its full text. The analysis runs as a background job with live progress, so leaving the page, a slow model or a server restart never loses an upload (a failed one can be retried from the stored PDF). Re-uploading a known paper (same file, DOI or arXiv id) reuses the analysis instead of calling the model again.
- **Chat with the paper itself, with citations.** Questions about a paper are answered from its full text, not just a summary: the paper is split into passages by section and page, the passages that best match the question are retrieved, and the answer streams in with numbered citations that open the exact passage it came from. Papers from the daily editions are fetched from arXiv the first time someone asks about them. Answers are pitched at the depth you picked.

## Screenshots

**Today's edition as a metro map.** Each research area is a line, each paper a station, ranked left to right. Hovering a station opens its board.

![Today's edition: the metro map with its station board](docs/screenshots/03-today-map.png)

**Every change, with a station rail** that follows you down the page.

![The list of changes with the sticky station rail](docs/screenshots/04-today-stations.png)

**One paper, three readers.** How each depth of the same paper begins.

![Plain, Student and Expert versions of the Transformer paper](docs/screenshots/02-three-readers.png)

**A paper page.** What changed, what it builds on, and the explanation at your depth.

![The paper page for Attention Is All You Need](docs/screenshots/05-paper.png)

**Chat with citations (RAG).** The answer cites numbered passages of the paper; each opens the exact text, section and page it came from.

![A streamed answer citing passages of the paper, with one source opened](docs/screenshots/06-paper-chat.png)

**Explain your own paper.** Uploads are processed as background jobs with live progress.

![An upload in progress beside earlier uploads](docs/screenshots/07-explain-progress.png)

**Your papers**, with delete.

![The library of explained papers](docs/screenshots/08-library.png)

**Every edition**, as a timetable.

![The timetable of editions](docs/screenshots/09-editions.png)

**On a phone**, the map becomes a vertical strip map.

![Home, today and a paper page on a phone](docs/screenshots/10-mobile.png)

## How an edition is made

```
arXiv (cs.AI, cs.LG, cs.CL, cs.CV)  ~400-600 papers a day
        │
        ▼
 Triage (1 model call)       pick the ~10 that change the field most
        │
        ▼
 Analyse (1 call per paper)  what changed · builds on · Plain / Student / Expert
        │
        ▼
 Front matter (1 call)       a specific headline, overview and themes
        │
        ▼
 Postgres / SQLite  ──►  FastAPI  ──►  Next.js line diagram
```

About a dozen model calls a day, so it runs comfortably on Gemini's free tier.

## How chat answers from the paper (RAG)

```mermaid
flowchart LR
    Q[Question] --> I{Paper indexed?}
    I -- no --> T[Full text<br/>upload, or PDF from arXiv]
    T --> S[Split into passages<br/>by section and page,<br/>reference list skipped]
    S --> E[Embed passages<br/>gemini-embedding-001]
    E --> DB[(paper_chunks)]
    I -- yes --> R
    DB --> R[Rank passages:<br/>BM25 keywords + embedding<br/>similarity, fused by rank]
    R --> P[Prompt with numbered<br/>passages + summary]
    P --> L[Gemini, streamed]
    L --> A[Answer with citations<br/>over server-sent events]
```

- **Passages that follow the paper.** Headings are detected from the PDF's own numbering (a section number has to follow on from the last one, so table values aren't mistaken for headings), every passage keeps its page, and the reference list is left out.
- **Hybrid retrieval.** Keyword ranking (BM25) catches exact terms like "BLEU" or "P100"; embedding similarity catches paraphrases. The two rankings are merged with reciprocal rank fusion. A paper has at most a few hundred passages, so they are ranked in Python per question and no vector database is needed; if embeddings are unavailable, keyword ranking carries on alone.
- **Grounded answers.** The model is told to cite the passage numbers it used and to say so when the paper doesn't contain the answer. Off-topic questions get "the paper doesn't say", not a guess.
- **Streaming.** The API sends server-sent events (`status`, `sources`, `delta`, `done`), so the answer appears as it is written; the first question about a paper also reports that it is reading the paper.

## Stack

| | |
| --- | --- |
| Web | Next.js 16 (App Router, Cache Components), React 19, TypeScript, Tailwind CSS 4 |
| API | FastAPI, Pydantic, SQLAlchemy 2, Alembic, JWT auth (PyJWT + bcrypt), per-user rate limits |
| Data | PostgreSQL in production, SQLite locally |
| AI | Google Gemini 3.1 Flash-Lite via `google-genai` (free Gemma 4 as the fallback when it is rate limited or overloaded); `gemini-embedding-001` and BM25 for retrieval |
| Quality | pytest (SQLite and Postgres), ruff, ESLint, TypeScript, GitHub Actions |

## Run it locally

You need Python 3.12+, Node 20+ and pnpm.

**1. API**

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # add GEMINI_API_KEY and SECRET_KEY
python -m scripts.seed             # creates the database and loads six real editions
uvicorn app.main:app --reload --port 8000
```

- `GEMINI_API_KEY`: from https://aistudio.google.com/apikey
- `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`

**2. Web**

```bash
cd web
pnpm install
pnpm dev                           # http://localhost:3000
```

The web app calls `/api/...` on its own origin and Next.js forwards those requests to the API (`API_URL`, default `http://127.0.0.1:8000`), so there is no CORS setup.

**3. Make today's edition**

```bash
python -m scripts.generate_edition             # the most recent day on arXiv
python -m scripts.generate_edition --days 5    # backfill the last five weekdays
```

## Tests and checks

```bash
pytest                                         # API: 86 tests, fake model, no key needed
ruff check app scripts tests migrations/env.py
cd web && pnpm exec eslint src && pnpm exec tsc --noEmit && pnpm build
```

CI runs the API tests on SQLite and on Postgres 17 (including migrations), and lints, type-checks and builds the web app.

## API

Interactive docs at `/docs` when the API is running.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/api/editions` | | Editions, newest first |
| GET | `/api/editions/latest` | | The latest edition with its ranked papers |
| GET | `/api/editions/{date}` | | One day's edition, with previous and next dates |
| POST | `/api/editions/{date}/chat` | ✓ | Ask about an edition (`message`, `level`) |
| POST | `/api/papers` | ✓ | Upload a PDF; answers at once with a job to poll |
| GET | `/api/papers/jobs`, `/api/papers/jobs/{id}` | ✓ | Your uploads and how far each has got |
| POST, DELETE | `/api/papers/jobs/{id}/retry`, `/api/papers/jobs/{id}` | ✓ | Retry a failed upload, or remove one from the list |
| GET | `/api/papers` | ✓ | Your uploaded papers |
| GET | `/api/papers/{id}` | | A paper with all three explanations |
| DELETE | `/api/papers/{id}` | ✓ | Remove a paper from your papers and delete your PDF |
| POST | `/api/papers/{id}/chat` | ✓ | Ask about a paper; the answer cites passages of its full text |
| POST | `/api/papers/{id}/chat/stream` | ✓ | The same answer as server-sent events, written as it arrives |
| POST | `/api/auth/register`, `/api/auth/token` | | Sign up, log in |
| GET | `/api/auth/me` | ✓ | Current user |

## Project layout

```
app/            FastAPI: routers (auth, editions, papers), services (editions pipeline,
                paper analysis, upload jobs, retrieval, chat), models, Alembic-managed schema
migrations/     Alembic migrations
scripts/        seed, generate_edition, export_seed, migrate
tests/          pytest suite
web/            Next.js app: src/app (routes), src/components (EditionMap, DepthSwitch, ...)
PRODUCT.md      Product positioning and principles
DESIGN.md       The design system: the transit-map world, tokens and components
```

## Design

The interface was designed with a "transit map" visual language: white signage ground, black signage bands, Archivo set like wayfinding signage, and line colours that never change meaning (Language red, Vision blue, Learning green, Agents orange, Robotics purple). Every text colour pairing meets WCAG AA, the diagram becomes a vertical strip map on phones, and all motion respects reduced-motion settings. See [DESIGN.md](DESIGN.md).

Explanations are written by a language model from each paper's abstract (or full text for uploads), and chat answers from passages of the paper's full text. Check the original paper before you cite it.
