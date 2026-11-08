# AcademixAI

AcademixAI makes research papers easier to read. It publishes a daily AI digest from new arXiv papers, turns any uploaded PDF into a plain-language summary, and lets you ask questions about a paper in a chat.

> This project is being rebuilt. The setup below runs the current version.

## Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **AI:** Google Gemini (`google-genai`) for summaries, digests and chat
- **PDF parsing:** PyMuPDF
- **Frontend:** server-rendered HTML, CSS and vanilla JavaScript

## Run it locally

You need Python 3.11 or newer.

```bash
git clone https://github.com/raghavsarna/AcademixAI.git
cd AcademixAI
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` from the template and fill it in:

```bash
cp .env.example .env
```

- `GEMINI_API_KEY`: get one at https://aistudio.google.com/apikey
- `SECRET_KEY`: generate one with `python -c "import secrets; print(secrets.token_hex(32))"`

Load the sample data and start the server:

```bash
python seed.py
uvicorn main:app --reload
```

Open http://localhost:8000.

## Generate a new daily digest

```bash
python arxiv_daily_summary.py
```

This fetches the latest AI papers from arXiv, summarises them with Gemini, and saves the digest to the database.

## Project layout

| Path | What it does |
| --- | --- |
| `main.py` | FastAPI app: page routes and the JSON API |
| `auth.py` | Password hashing and JWT login tokens |
| `pdf_processor.py` | PDF upload → text extraction → Gemini analysis → database |
| `arxiv_daily_summary.py` | Daily arXiv digest generator |
| `llm.py` | The single wrapper around the Gemini API |
| `config.py` | Settings read from `.env` |
| `models.py`, `schemas.py`, `database.py` | Database models, API schemas, DB session |
| `seed.py`, `data/seed.json` | Sample digests and papers |
| `pages/`, `static/`, `images/` | Frontend templates, styles and assets |
