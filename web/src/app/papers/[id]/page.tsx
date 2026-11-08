import { ExternalLink } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { Transfers } from "@/components/Transfers";
import { LineBullet } from "@/components/LineBullet";
import { Markdown } from "@/components/Markdown";
import { PaperReader } from "@/components/PaperReader";
import { PaperSkeleton } from "@/components/Skeletons";
import { getPaper } from "@/lib/api";
import { linesForPaper } from "@/lib/lines";
import { CHANGE_TYPE_LABELS, type PaperDetail } from "@/lib/types";


export async function generateMetadata({ params }: PageProps<"/papers/[id]">): Promise<Metadata> {
  const { id } = await params;
  const paper = await getPaper(id);
  return paper ? { title: paper.title, description: paper.what_changed ?? undefined } : {};
}

export default function PaperPage({ params }: PageProps<"/papers/[id]">) {
  return (
    <Suspense fallback={<PaperSkeleton />}>
      <Paper params={params} />
    </Suspense>
  );
}

async function Paper({ params }: { params: PageProps<"/papers/[id]">["params"] }) {
  const { id } = await params;
  const paper = await getPaper(id);
  if (!paper) notFound();
  const lines = paper.categories.length ? linesForPaper(paper.categories).slice(0, 2) : [];

  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-10 sm:px-8 sm:pt-14">
      <div className="grid gap-12 lg:grid-cols-[minmax(0,40rem)_18rem] lg:justify-center lg:gap-16">
        <article className="min-w-0">
          <header>
            <h1 className="text-[2rem] font-extrabold leading-[1.08] tracking-[-0.03em] sm:text-[2.75rem]">
              {paper.title}
            </h1>
            {paper.authors.length ? (
              <p className="mt-4 leading-relaxed text-ink-soft">
                {paper.authors.slice(0, 8).join(", ")}
                {paper.authors.length > 8 ? ` and ${paper.authors.length - 8} more` : ""}
              </p>
            ) : null}
          </header>

          <section aria-labelledby="changed-title" className="mt-8 border-t-[6px] border-band bg-panel p-5 sm:p-6">
            <h2 id="changed-title" className="text-lg font-bold">
              What changed
            </h2>
            <p className="mt-2 text-lg font-medium leading-relaxed">{paper.what_changed ?? "Not stated."}</p>
            {paper.why_it_matters ? <p className="mt-3 leading-relaxed text-ink-soft">{paper.why_it_matters}</p> : null}
            <Transfers items={paper.builds_on} />
          </section>

          <div className="mt-14">
            <Suspense fallback={<div className="h-96 bg-panel" />}>
              <PaperReader paper={paper} />
            </Suspense>
          </div>

          <MoreDetail paper={paper} />
        </article>

        <aside aria-label="About this paper" className="lg:pt-2">
          <div className="grid gap-6 border-t border-rule-strong pt-5 lg:sticky lg:top-6">
            {lines.length ? (
              <div>
                <h2 className="text-sm font-bold">Lines</h2>
                <ul className="mt-2 grid gap-2">
                  {lines.map((line) => (
                    <li key={line}>
                      <LineBullet line={line} size="md" label />
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <dl className="grid gap-4 text-sm">
              {paper.change_type ? <Fact label="Kind of change">{CHANGE_TYPE_LABELS[paper.change_type]}</Fact> : null}
              {paper.source ? <Fact label="Published in">{paper.source}</Fact> : null}
              {paper.publication_date ? <Fact label="Date">{paper.publication_date}</Fact> : null}
              {paper.arxiv_id ? <Fact label="arXiv">{paper.arxiv_id}</Fact> : null}
              {paper.keywords.length ? <Fact label="Keywords">{paper.keywords.join(", ")}</Fact> : null}
            </dl>
            {paper.source_url ? (
              <a
                href={paper.source_url}
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 font-semibold text-link underline"
              >
                Read the original paper <ExternalLink className="size-4" aria-hidden />
              </a>
            ) : null}
            <p className="text-sm leading-relaxed text-ink-soft">
              Explanations are written by a language model from the paper{paper.origin === "arxiv" ? "’s abstract" : ""}.
              Check the original before you cite it.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="font-bold">{label}</dt>
      <dd className="mt-0.5 text-ink-soft">{children}</dd>
    </div>
  );
}

function MoreDetail({ paper }: { paper: PaperDetail }) {
  const sections = [
    { id: "findings", title: "Main findings", body: paper.main_findings },
    { id: "method", title: "How they did it", body: paper.methodology },
  ].filter((s) => s.body);
  return (
    <div className="mt-14 grid gap-12">
      {sections.map((s) => (
        <section key={s.id} aria-labelledby={`${s.id}-title`}>
          <h2 id={`${s.id}-title`} className="text-2xl font-bold">
            {s.title}
          </h2>
          <div className="mt-4">
            <Markdown>{s.body as string}</Markdown>
          </div>
        </section>
      ))}
      {paper.abstract ? (
        <details className="group border-t border-rule pt-4">
          <summary className="cursor-pointer text-lg font-bold">The paper&rsquo;s own abstract</summary>
          <div className="mt-4">
            <Markdown>{paper.abstract}</Markdown>
          </div>
        </details>
      ) : null}
    </div>
  );
}
