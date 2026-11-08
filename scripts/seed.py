"""Bring the database schema up to date and load the sample editions and papers.

Usage:
    python -m scripts.seed           # add any sample rows that are missing
    python -m scripts.seed --reset   # delete existing editions and papers first
"""

import argparse
import json
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Edition, EditionEntry, Paper, Upload
from scripts.migrate import upgrade_to_head

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"


def seed(reset: bool = False) -> tuple[int, int]:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        if reset:
            for model in (EditionEntry, Edition, Upload, Paper):
                db.execute(delete(model))

        added_papers = 0
        for item in data["papers"]:
            if db.get(Paper, item["id"]) is None:
                db.add(Paper(**item))
                added_papers += 1
        db.flush()

        added_editions = 0
        for item in data["editions"]:
            day = date.fromisoformat(item["edition_date"])
            if db.scalar(select(Edition).where(Edition.edition_date == day)):
                continue
            edition = Edition(
                edition_date=day,
                headline=item["headline"],
                overview=item["overview"],
                themes=item["themes"],
                papers_scanned=item["papers_scanned"],
            )
            edition.entries = [EditionEntry(paper_id=pid, rank=i) for i, pid in enumerate(item["entries"], 1)]
            db.add(edition)
            added_editions += 1

        db.commit()
    return added_editions, added_papers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete existing editions and papers first")
    args = parser.parse_args()

    upgrade_to_head()
    editions, papers = seed(reset=args.reset)
    print(f"Seeded {editions} editions and {papers} papers.")


if __name__ == "__main__":
    main()
