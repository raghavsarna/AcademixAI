import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { EditionView } from "@/components/EditionView";
import { EditionSkeleton } from "@/components/Skeletons";
import { getLatestEdition } from "@/lib/api";

export const metadata: Metadata = { title: "Today's edition" };

export default function TodayPage() {
  return (
    <Suspense fallback={<EditionSkeleton />}>
      <LatestEdition />
    </Suspense>
  );
}

async function LatestEdition() {
  const edition = await getLatestEdition();
  if (!edition) {
    return (
      <div className="mx-auto max-w-[88rem] px-5 py-20 sm:px-8">
        <h1 className="text-4xl font-extrabold tracking-[-0.03em]">The first edition hasn&rsquo;t run yet</h1>
        <p className="mt-4 max-w-prose text-lg leading-relaxed text-ink-soft">
          Editions are built each day from new arXiv papers. Generate one with{" "}
          <code className="rounded-[3px] bg-panel px-1.5 py-0.5">python -m scripts.generate_edition</code>, or explain
          a paper of your own in the meantime.
        </p>
        <Link href="/explain" className="mt-6 inline-block font-semibold text-link underline">
          Explain a paper
        </Link>
      </div>
    );
  }
  return <EditionView edition={edition} path="/today" />;
}
