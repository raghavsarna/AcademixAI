import { ArrowLeft, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { formatEditionDate, numberFormat } from "@/lib/format";
import { linesForPaper, paperStationName } from "@/lib/lines";
import type { EditionDetail } from "@/lib/types";

import { EditionChat } from "./EditionChat";
import { EditionMap } from "./EditionMap";
import { SignBand } from "./SignBand";
import { StationRail } from "./StationRail";
import { StationEntry } from "./StationEntry";

function lineCount(edition: EditionDetail): number {
  const lines = new Set(edition.entries.flatMap((e) => linesForPaper(e.paper.categories).slice(0, 2)));
  return lines.size;
}

export function EditionView({ edition, path }: { edition: EditionDetail; path: string }) {
  const date = formatEditionDate(edition.edition_date);
  const titles = new Map(edition.entries.map((e) => [e.paper.id, e.paper.title]));

  return (
    <div className="mx-auto max-w-[88rem] px-5 sm:px-8">
      <header className="grid gap-6 pb-10 pt-10 sm:pt-14 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="max-w-4xl">
          <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
            {edition.headline}
          </h1>
          <p className="mt-4 text-lg font-semibold">
            <time dateTime={edition.edition_date}>{date}</time>
            <span className="text-ink-soft">
              {" "}
              · {edition.entries.length} changes from {numberFormat.format(edition.papers_scanned)} new papers · {lineCount(edition)} lines
            </span>
          </p>
          <p className="mt-5 max-w-[60ch] text-lg leading-relaxed">{edition.overview}</p>
        </div>
        <EditionNav previous={edition.previous_date} next={edition.next_date} />
      </header>

      <section aria-labelledby="map-title">
        <EditionMap
          entries={edition.entries}
          editionLabel={`the edition of ${date}`}
          band={
            <SignBand title="The map" id="map-title">
              <p className="text-band-soft">Hover or focus a station to read its board.</p>
            </SignBand>
          }
        />
      </section>

      {edition.themes.length ? (
        <section aria-labelledby="themes-title" className="mt-16">
          <SignBand title="Through-lines" id="themes-title" />
          <dl className="mt-6 grid gap-x-10 gap-y-8 md:grid-cols-2">
            {edition.themes.map((theme) => (
              <div key={theme.name} className="border-t border-rule-strong pt-4">
                <dt className="text-lg font-bold">{theme.name}</dt>
                <dd className="mt-1.5 max-w-[60ch] leading-relaxed text-ink-soft">{theme.summary}</dd>
                <dd className="mt-2 max-w-[60ch] text-sm font-semibold">
                  {theme.papers
                    .map((id) => titles.get(id))
                    .filter(Boolean)
                    .join(" · ")}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      <section aria-labelledby="stations-title" className="mt-16">
        <SignBand title="Every change, most significant first" id="stations-title" />
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_17rem]">
          <ol>
            {edition.entries.map((entry) => (
              <li key={entry.paper.id}>
                <StationEntry rank={entry.rank} paper={entry.paper} />
              </li>
            ))}
          </ol>
          <div className="hidden pt-8 lg:block">
            <StationRail
              stations={edition.entries.map((e) => ({
                rank: e.rank,
                name: paperStationName(e.paper),
                lines: linesForPaper(e.paper.categories).slice(0, 2),
              }))}
            />
          </div>
        </div>
      </section>

      <section className="mt-12" aria-label="Chat">
        <Suspense fallback={<div className="h-48 bg-panel" />}>
          <EditionChat date={edition.edition_date} path={path} />
        </Suspense>
      </section>

      <div className="mt-12 flex justify-between border-t border-rule pt-6">
        <EditionNav previous={edition.previous_date} next={edition.next_date} />
      </div>
    </div>
  );
}

function EditionNav({ previous, next }: { previous: string | null; next: string | null }) {
  const base = "inline-flex items-center gap-2 rounded-[4px] border px-3.5 py-2 text-sm font-semibold no-underline";
  return (
    <nav aria-label="Other editions" className="flex flex-wrap gap-2">
      {previous ? (
        <Link href={`/editions/${previous}`} className={`${base} border-rule-strong text-ink hover:border-ink`}>
          <ArrowLeft className="size-4" aria-hidden strokeWidth={2.5} /> {formatEditionDate(previous, "short")}
        </Link>
      ) : (
        <span className={`${base} border-rule text-ink-soft`} aria-disabled>
          First edition
        </span>
      )}
      {next ? (
        <Link href={`/editions/${next}`} className={`${base} border-rule-strong text-ink hover:border-ink`}>
          {formatEditionDate(next, "short")} <ArrowRight className="size-4" aria-hidden strokeWidth={2.5} />
        </Link>
      ) : (
        <Link href="/editions" className={`${base} border-rule-strong text-ink hover:border-ink`}>
          All editions
        </Link>
      )}
    </nav>
  );
}
