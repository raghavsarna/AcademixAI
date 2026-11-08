import Link from "next/link";
import { Suspense } from "react";

import { DepthDemo } from "@/components/DepthDemo";
import { EditionMap } from "@/components/EditionMap";
import { EditionTimetable } from "@/components/EditionTimetable";
import { PipelineStrip } from "@/components/PipelineStrip";
import { SignBand } from "@/components/SignBand";
import { getLatestEdition, getPaper, listEditions } from "@/lib/api";
import { formatEditionDate, numberFormat } from "@/lib/format";
import { linesForPaper } from "@/lib/lines";

// The paper that introduced the Transformer: a sample most readers have heard of.
const DEMO_PAPER_ID = "8d8b360c517f55a1b37e57f5240020eb";

function HeroIntro() {
  return (
    <div className="grid gap-x-12 gap-y-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-end">
      <h1 className="max-w-[17ch] text-[2.75rem] font-extrabold leading-[0.98] tracking-[-0.035em] sm:text-[3.5rem] xl:text-[3.875rem]">
        See what changed in AI research today.
      </h1>
      <div>
        <p className="max-w-[60ch] text-lg leading-relaxed">
          Each day we read the new arXiv papers in AI, machine learning, language and vision, pick the ones that move
          the field, and draw them on one map. Open any paper and read it Plain, Student or Expert.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
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
    </div>
  );
}

export default function Home() {
  return (
    <>
      <section className="mx-auto max-w-[88rem] px-5 pb-16 pt-8 sm:px-8 sm:pt-10">
        <Suspense
          fallback={
            <>
              <HeroIntro />
              <div className="mt-8 h-[30rem] rounded-[3px] bg-panel motion-safe:animate-pulse" aria-busy="true" />
            </>
          }
        >
          <HeroMap />
        </Suspense>
      </section>

      <section className="mx-auto max-w-[88rem] px-5 pb-20 sm:px-8" aria-labelledby="readers-title">
        <SignBand title="One paper, three readers" id="readers-title">
          <p className="text-band-soft">Try it on the paper that introduced the Transformer.</p>
        </SignBand>
        <div className="mt-8">
          <Suspense fallback={<div className="h-96 bg-panel" />}>
            <Demo />
          </Suspense>
        </div>
      </section>

      <section className="mx-auto max-w-[88rem] px-5 pb-20 sm:px-8" aria-labelledby="made-title">
        <SignBand title="How each edition is made" id="made-title" />
        <p className="mt-6 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
          No newsletter roundup of everything published. A changelog of what moved, built the same way every day.
        </p>
        <div className="mt-10">
          <Suspense fallback={<div className="h-32 bg-panel" />}>
            <Pipeline />
          </Suspense>
        </div>
      </section>

      <section className="mx-auto max-w-[88rem] px-5 pb-8 sm:px-8" aria-labelledby="recent-title">
        <SignBand title="Recent editions" id="recent-title">
          <Link href="/editions" className="font-semibold text-white underline decoration-signal decoration-2">
            All editions
          </Link>
        </SignBand>
        <div className="mt-2">
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

async function HeroMap() {
  const edition = await getLatestEdition();
  if (!edition) return <HeroIntro />;
  const date = formatEditionDate(edition.edition_date);
  return (
    <EditionMap
      entries={edition.entries}
      editionLabel={`the edition of ${date}`}
      intro={<HeroIntro />}
      band={
        <SignBand title={<time dateTime={edition.edition_date}>{date}</time>}>
          <p className="max-w-[70ch] text-band-soft">
            <Link href="/today" className="font-semibold text-white no-underline hover:underline">
              {edition.headline}
            </Link>
            <span className="tabular">
              {" "}
              · {edition.entries.length} changes from {numberFormat.format(edition.papers_scanned)} new papers
            </span>
          </p>
        </SignBand>
      }
    />
  );
}

async function Demo() {
  const paper = await getPaper(DEMO_PAPER_ID);
  if (!paper) return null;
  return <DepthDemo paper={paper} />;
}

async function Pipeline() {
  const edition = await getLatestEdition();
  const lines = edition ? new Set(edition.entries.flatMap((e) => linesForPaper(e.paper.categories).slice(0, 2))).size : 5;
  return <PipelineStrip scanned={edition?.papers_scanned ?? 0} changes={edition?.entries.length ?? 10} lines={lines} />;
}

async function Recent() {
  const editions = await listEditions(5);
  if (!editions.length) return <p className="mt-6 text-lg">The first edition appears after the daily run.</p>;
  return <EditionTimetable editions={editions} caption="The five most recent editions" header="plain" />;
}
