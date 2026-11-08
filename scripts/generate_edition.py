"""Generate the daily edition: what changed in AI research, from new arXiv papers.

Usage:
    python -m scripts.generate_edition                   # the most recent day with submissions
    python -m scripts.generate_edition --date 2026-11-05 # a specific day
    python -m scripts.generate_edition --days 5          # backfill the last 5 weekdays
Options:
    --picks N    papers per edition (default 10)
    --replace    rebuild an edition that already exists
"""

import argparse
import asyncio
import logging
from datetime import date

from app.db import SessionLocal
from app.services.editions import build_edition, recent_days


async def run(days: list[date | None], picks: int, replace: bool) -> None:
    for day in days:
        with SessionLocal() as db:
            try:
                edition = await build_edition(db, day=day, picks=picks, replace=replace)
            except RuntimeError as e:
                print(f"{day or 'latest'}: skipped ({e})")
                continue
            print(f"{edition.edition_date}: {len(edition.entries)} entries from {edition.papers_scanned} papers")
            print(f"  {edition.headline}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "arxiv", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", type=date.fromisoformat, help="edition date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="backfill this many recent weekdays")
    parser.add_argument("--picks", type=int, default=10)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    days: list[date | None] = recent_days(args.days) if args.days else [args.date]
    asyncio.run(run(list(reversed(days)), args.picks, args.replace))


if __name__ == "__main__":
    main()
