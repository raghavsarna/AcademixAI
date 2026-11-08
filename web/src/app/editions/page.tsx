import type { Metadata } from "next";
import { Suspense } from "react";

import { EditionTimetable } from "@/components/EditionTimetable";
import { ListSkeleton } from "@/components/Skeletons";
import { listEditions } from "@/lib/api";

export const metadata: Metadata = { title: "All editions" };

export default function EditionsPage() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-10 sm:px-8 sm:pt-14">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
        Every edition
      </h1>
      <p className="mt-4 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
        One edition for each day of new arXiv papers in AI, machine learning, language and vision. Read down the
        timetable to see how the field moved.
      </p>
      <Suspense fallback={<div className="mt-8"><ListSkeleton /></div>}>
        <Timetable />
      </Suspense>
    </div>
  );
}

async function Timetable() {
  const editions = await listEditions();
  if (!editions.length) {
    return <p className="mt-10 text-lg">No editions yet. The first one appears after the daily run.</p>;
  }
  return (
    <div className="mt-10">
      <EditionTimetable editions={editions} caption="Editions, newest first" />
    </div>
  );
}
