import Link from "next/link";

import { LINES, linesForPaper } from "@/lib/lines";
import { CHANGE_TYPE_LABELS, type PaperCard } from "@/lib/types";

import { LineBullets } from "./LineBullet";
import { Transfers } from "./Transfers";


/** One changed paper in an edition, set like a station listing. */
export function StationEntry({ rank, paper }: { rank: number; paper: PaperCard }) {
  const lines = linesForPaper(paper.categories).slice(0, 2);
  const meta = [
    paper.change_type ? CHANGE_TYPE_LABELS[paper.change_type] : null,
    lines.map((l) => LINES[l].name).join(" + "),
    paper.arxiv_id ? `arXiv ${paper.arxiv_id}` : null,
  ].filter(Boolean);

  return (
    <article
      id={`station-${rank}`}
      data-rank={rank}
      className="grid scroll-mt-6 grid-cols-[3rem_1fr] gap-x-4 border-b border-rule py-8 sm:grid-cols-[4.5rem_1fr] sm:gap-x-6"
    >
      <div className="flex flex-col items-start gap-3">
        <span className="tabular text-3xl font-extrabold leading-none text-ink-soft sm:text-4xl" aria-label={`Number ${rank}`}>
          {rank}
        </span>
        <LineBullets lines={lines} size="md" />
      </div>
      <div className="min-w-0">
        <h3 className="text-xl font-bold leading-snug sm:text-[1.375rem]">
          <Link href={`/papers/${paper.id}`} className="text-ink no-underline hover:underline">
            {paper.title}
          </Link>
        </h3>
        <p className="mt-1.5 text-sm font-semibold text-ink-soft">{meta.join(" · ")}</p>
        <p className="mt-4 max-w-[60ch] text-[1.0625rem] font-medium leading-relaxed">{paper.what_changed}</p>
        {paper.why_it_matters ? (
          <p className="mt-2 max-w-[60ch] leading-relaxed text-ink-soft">{paper.why_it_matters}</p>
        ) : null}
        <Transfers items={paper.builds_on} />
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 font-semibold">
          <Link href={`/papers/${paper.id}`} className="text-link underline">
            Read it at your level
          </Link>
          {paper.source_url ? (
            <a href={paper.source_url} className="text-ink-soft underline hover:text-ink" rel="noopener noreferrer">
              Paper on arXiv
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
