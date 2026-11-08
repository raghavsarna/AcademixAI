import Link from "next/link";
import { Suspense } from "react";

import { DepthDemo } from "@/components/DepthDemo";
import { EditionMap } from "@/components/EditionMap";
import { EditionTimetable } from "@/components/EditionTimetable";
import { PipelineStrip } from "@/components/PipelineStrip";
import { getLatestEdition, getPaper, listEditions } from "@/lib/api";
import { formatEditionDate, numberFormat } from "@/lib/format";
import { linesForPaper } from "@/lib/lines";

// The paper that introduced the Transformer: a sample most readers have heard of.
const DEMO_PAPER_ID = "8d8b360c517f55a1b37e57f5240020eb";

export default function Home() {
  return (
    <>
      <section className="mx-auto max-w-[88rem] px-5 pb-16 pt-8 sm:px-8 sm:pt-10">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(19rem,1fr)] lg:items-end">
          <div>
            <h1 className="max-w-[17ch] text-[2.75rem] font-extrabold leading-[0.98] tracking-[-0.035em] sm:text-[3.75rem] xl:text-[4.25rem]">
              See what changed in AI research today.
            </h1>
            <p className="mt-5 max-w-[62ch] text-lg leading-relaxed">
              Each day we read the new arXiv papers in AI, machine learning, language and vision, pick the ones that
              move the field, and draw them on one map. Open any paper and read it Plain, Student or Expert.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                href="/today"
                className="rounded-[4px] bg-band px-6 py-3.5 text-lg font-bold text-white no-underline transition-colors duration-150 hover:bg-ink"
              >
                Ride today&rsquo;s changes
              </Link>
              <Link
                href="/explain"
                className="rounded-[4px] border-2 border-band px-6 py-3.5 text-lg font-bold text-ink no-underline transition-colors duration-150 hover:bg-panel"
              >
                Explain a paper
              </Link>
            </div>
          </div>
          <Suspense fallback={<div className="h-40 bg-panel" />}>
            <LatestBulletin />
          </Suspense>
        </div>
        <div className="mt-10">
          <Suspense fallback={<div className="h-80 bg-panel motion-safe:animate-pulse" />}>
            <LatestMap />
          </Suspense>
        </div>
      </section>

      <section className="border-y border-rule bg-ground">
        <div className="mx-auto max-w-[88rem] px-5 py-20 sm:px-8">
          <Suspense fallback={<div className="h-96 bg-panel" />}>
            <Demo />
          </Suspense>
        </div>
      </section>

      <section className="mx-auto max-w-[88rem] px-5 py-20 sm:px-8">
        <h2 className="text-[2rem] font-extrabold leading-[1.08] tracking-[-0.03em] sm:text-[2.5rem]">
          How each edition is made
        </h2>
        <p className="mt-4 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
          No newsletter roundup of everything published. A changelog of what moved, built the same way every day.
        </p>
        <div className="mt-12">
          <Suspense fallback={<div className="h-32 bg-panel" />}>
            <Pipeline />
          </Suspense>
        </div>
      </section>

      <section className="mx-auto max-w-[88rem] px-5 pb-8 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="text-[2rem] font-extrabold leading-[1.08] tracking-[-0.03em] sm:text-[2.5rem]">Recent editions</h2>
          <Link href="/editions" className="font-semibold text-link underline">
            All editions
          </Link>
        </div>
        <div className="mt-8">
          <Suspense fallback={<div className="h-64 bg-panel" />}>
            <Recent />
          </Suspense>
        </div>
      </section>

      <section className="mx-auto mt-16 max-w-[88rem] px-5 sm:px-8">
        <div className="grid gap-6 bg-band p-8 text-white sm:p-12 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <h2 className="text-[1.75rem] font-extrabold leading-tight tracking-[-0.02em] sm:text-[2.25rem]">
              Stuck on a paper of your own?
            </h2>
            <p className="mt-3 max-w-[56ch] text-lg leading-relaxed text-band-soft">
              Upload the PDF. You get what it changes, what it builds on, the explanation at all three depths, and a
              chat that answers at yours.
            </p>
          </div>
          <Link
            href="/explain"
            className="justify-self-start rounded-[4px] bg-signal px-6 py-3.5 text-lg font-bold text-ink no-underline transition-colors duration-150 hover:bg-white"
          >
            Explain a paper
          </Link>
        </div>
      </section>
    </>
  );
}

async function LatestBulletin() {
  const edition = await getLatestEdition();
  if (!edition) return null;
  return (
    <div className="border-t-[6px] border-band bg-panel p-5">
      <h2 className="text-sm font-bold">
        Latest edition, <time dateTime={edition.edition_date}>{formatEditionDate(edition.edition_date)}</time>
      </h2>
      <p className="mt-2 text-xl font-bold leading-snug">
        <Link href="/today" className="text-ink no-underline hover:underline">
          {edition.headline}
        </Link>
      </p>
      <p className="tabular mt-2 text-sm text-ink-soft">
        {edition.entries.length} changes from {numberFormat.format(edition.papers_scanned)} new papers
      </p>
    </div>
  );
}

async function LatestMap() {
  const edition = await getLatestEdition();
  if (!edition) return null;
  return <EditionMap entries={edition.entries} editionLabel={`the edition of ${formatEditionDate(edition.edition_date)}`} />;
}

async function Demo() {
  const paper = await getPaper(DEMO_PAPER_ID);
  if (!paper) return null;
  return <DepthDemo paper={paper} />;
}

async function Pipeline() {
  const edition = await getLatestEdition();
  const lines = edition ? new Set(edition.entries.flatMap((e) => linesForPaper(e.paper.categories).slice(0, 2))).size : 5;
  return (
    <PipelineStrip
      scanned={edition?.papers_scanned ?? 0}
      changes={edition?.entries.length ?? 10}
      lines={lines}
    />
  );
}

async function Recent() {
  const editions = await listEditions(5);
  if (!editions.length) return <p className="text-lg">The first edition appears after the daily run.</p>;
  return <EditionTimetable editions={editions} caption="The five most recent editions" />;
}
