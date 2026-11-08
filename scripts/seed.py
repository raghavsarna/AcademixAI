"""Bring the database schema up to date and load sample digests and papers.

Usage:
    python -m scripts.seed           # add any sample rows that are missing
    python -m scripts.seed --reset   # delete existing digests and papers first
"""

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Digest, Paper, Upload
from scripts.migrate import upgrade_to_head

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"


def sample_paper_id(title: str) -> str:
    """Stable id so sample paper URLs stay the same between seeds."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"academixai:sample:{title}").hex


def seed(reset: bool = False) -> tuple[int, int]:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        if reset:
            db.execute(delete(Upload))
            db.execute(delete(Paper))
            db.execute(delete(Digest))

        added_digests = 0
        for item in data["digests"]:
            if db.scalar(select(Digest).where(Digest.title == item["title"])):
                continue
            db.add(Digest(**{**item, "published_at": datetime.fromisoformat(item["published_at"])}))
            added_digests += 1

        added_papers = 0
        for item in data["papers"]:
            paper_id = sample_paper_id(item["title"])
            if db.get(Paper, paper_id):
                continue
            db.add(Paper(id=paper_id, **item))
            added_papers += 1

        db.commit()
    return added_digests, added_papers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete existing digests and papers first")
    args = parser.parse_args()

    upgrade_to_head()
    digests, papers = seed(reset=args.reset)
    print(f"Seeded {digests} digests and {papers} papers.")


if __name__ == "__main__":
    main()
