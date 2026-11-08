import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { EditionView } from "@/components/EditionView";
import { EditionSkeleton } from "@/components/Skeletons";
import { getEdition } from "@/lib/api";
import { formatEditionDate } from "@/lib/format";

export async function generateMetadata({ params }: PageProps<"/editions/[date]">): Promise<Metadata> {
  const { date } = await params;
  return /^\d{4}-\d{2}-\d{2}$/.test(date) ? { title: `Edition of ${formatEditionDate(date)}` } : {};
}

export default function EditionPage({ params }: PageProps<"/editions/[date]">) {
  return (
    <Suspense fallback={<EditionSkeleton />}>
      <Edition params={params} />
    </Suspense>
  );
}

async function Edition({ params }: { params: PageProps<"/editions/[date]">["params"] }) {
  const { date } = await params;
  const edition = /^\d{4}-\d{2}-\d{2}$/.test(date) ? await getEdition(date) : null;
  if (!edition) notFound();
  return <EditionView edition={edition} path={`/editions/${date}`} />;
}
