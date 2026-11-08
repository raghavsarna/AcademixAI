"""Give papers that were analysed before station names existed a short name for the metro map.

Asks the model for names in batches, so a whole seed set costs a handful of calls.

Usage:
    python -m scripts.name_stations
"""

import asyncio
import json

from sqlalchemy import select

from app import llm
from app.db import SessionLocal
from app.models import Paper
from app.services.analysis import SHORT_NAME_SPEC, normalize_short_name, parse_json_reply

BATCH = 20

PROMPT = """For each paper below, write {spec}

Reply with ONLY a JSON object mapping each paper's id to its name.

{papers}"""


async def name_batch(papers: list[Paper]) -> dict[str, str]:
    listing = "\n\n".join(f"id: {p.id}\ntitle: {p.title}\nwhat changed: {p.what_changed or ''}" for p in papers)
    reply = await llm.generate(PROMPT.format(spec=SHORT_NAME_SPEC, papers=listing), json_output=True)
    names = {}
    for paper_id, value in parse_json_reply(reply).items():
        name = normalize_short_name(value)
        if name:
            names[paper_id] = name
    return names


async def run() -> None:
    with SessionLocal() as db:
        papers = list(db.scalars(select(Paper).where(Paper.short_name.is_(None))))
        named = 0
        for start in range(0, len(papers), BATCH):
            batch = papers[start : start + BATCH]
            names = await name_batch(batch)
            for paper in batch:
                if paper.id in names:
                    paper.short_name = names[paper.id]
                    named += 1
            db.commit()
        print(f"Named {named} of {len(papers)} papers.")
        print(json.dumps({p.title[:60]: p.short_name for p in papers}, indent=1, ensure_ascii=False))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
