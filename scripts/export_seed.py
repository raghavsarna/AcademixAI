"""Write the current database's editions and sample papers to data/seed.json.

Exports every edition, the arXiv papers they reference, and sample papers (analysed
papers that no user owns). Papers uploaded by a user are never exported.

Usage:
    python -m scripts.export_seed
"""

import json

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Edition, EditionEntry, Paper, Upload
from scripts.seed import SEED_FILE

PAPER_FIELDS = (
    "id", "doi", "title", "authors", "source", "publication_date", "keywords", "abstract", "origin",
    "arxiv_id", "source_url", "categories", "short_name", "what_changed", "change_type", "why_it_matters", "builds_on",
    "explanations", "main_findings", "methodology",
)  # fmt: skip


def main() -> None:
    with SessionLocal() as db:
        owned = set(db.scalars(select(Upload.paper_id)))
        in_editions = set(db.scalars(select(EditionEntry.paper_id)))
        papers = [
            p
            for p in db.scalars(select(Paper).order_by(Paper.created_at))
            if p.id not in owned and (p.id in in_editions or p.origin == "upload")
        ]
        editions = list(db.scalars(select(Edition).order_by(Edition.edition_date)))
        data = {
            "papers": [{field: getattr(p, field) for field in PAPER_FIELDS} for p in papers],
            "editions": [
                {
                    "edition_date": e.edition_date.isoformat(),
                    "headline": e.headline,
                    "overview": e.overview,
                    "themes": e.themes,
                    "papers_scanned": e.papers_scanned,
                    "entries": [entry.paper_id for entry in e.entries],
                }
                for e in editions
            ],
        }
    SEED_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(data['editions'])} editions and {len(data['papers'])} papers to {SEED_FILE}")


if __name__ == "__main__":
    main()
