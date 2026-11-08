"""Create the database tables and load sample digests and papers from data/seed.json.

Usage:
    python seed.py           # add any sample rows that are missing
    python seed.py --reset   # delete existing digests and papers first
"""
import argparse
import datetime
import json
from pathlib import Path

from database import SessionLocal, create_tables
from models import Newsletter, Paper, UserUpload

SEED_FILE = Path(__file__).parent / "data" / "seed.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete existing digests and papers before seeding")
    args = parser.parse_args()

    create_tables()
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        if args.reset:
            db.query(UserUpload).delete()
            db.query(Paper).delete()
            db.query(Newsletter).delete()

        added_newsletters = 0
        for item in seed["newsletters"]:
            if db.query(Newsletter).filter(Newsletter.title == item["title"]).first():
                continue
            db.add(Newsletter(
                title=item["title"],
                picture=item["picture"],
                content=item["content"],
                description=item["description"],
                date=datetime.datetime.fromisoformat(item["date"]),
            ))
            added_newsletters += 1

        added_papers = 0
        for item in seed["papers"]:
            if db.query(Paper).filter(Paper.doi == item["doi"]).first():
                continue
            db.add(Paper(**item))
            added_papers += 1

        db.commit()
        print(f"Seeded {added_newsletters} digests and {added_papers} papers.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
