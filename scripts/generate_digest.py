"""Generate today's AI research digest from new arXiv papers and save it.

Usage:
    python -m scripts.generate_digest [--max-papers 150]
"""

import argparse
import asyncio
import logging

from app.db import SessionLocal
from app.services.digests import generate_digest


async def run(max_papers: int) -> None:
    with SessionLocal() as db:
        digest = await generate_digest(db, max_papers=max_papers)
    print(f"Saved digest {digest.id}: {digest.title}")
    print(f"View it at /content?summary_id={digest.id}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-papers", type=int, default=150, help="how many recent arXiv papers to consider")
    args = parser.parse_args()
    asyncio.run(run(args.max_papers))


if __name__ == "__main__":
    main()
