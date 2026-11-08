"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/client-api";
import { formatTimestamp } from "@/lib/format";
import type { MyPaper } from "@/lib/types";

import { ListSkeleton } from "./Skeletons";

export function MyPapers() {
  const [papers, setPapers] = useState<MyPaper[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .myPapers()
      .then(setPapers)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load your papers. Try again."));
  }, []);

  if (error) {
    return (
      <p className="mt-8 font-semibold text-danger" role="alert">
        {error}
      </p>
    );
  }
  if (!papers) return <ListSkeleton />;

  if (!papers.length) {
    return (
      <div className="mt-8 max-w-2xl border-t-[6px] border-band bg-panel p-6">
        <h2 className="text-xl font-bold">No papers yet</h2>
        <p className="mt-2 leading-relaxed text-ink-soft">
          Upload a PDF and it shows up here with what it changes and its three explanations, ready to come back to.
        </p>
        <Link href="/explain" className="mt-4 inline-block font-semibold text-link underline">
          Explain your first paper
        </Link>
      </div>
    );
  }

  return (
    <ul className="mt-8 border-b border-rule">
      {papers.map((p) => (
        <li key={p.id} className="grid gap-1 border-t border-rule py-5 sm:grid-cols-[1fr_auto] sm:gap-6">
          <div className="min-w-0">
            <Link href={`/papers/${p.id}`} className="text-lg font-bold text-ink no-underline hover:underline">
              {p.title}
            </Link>
            {p.what_changed ? <p className="mt-1 max-w-[80ch] leading-relaxed text-ink-soft">{p.what_changed}</p> : null}
          </div>
          <p className="text-sm text-ink-soft sm:text-right">
            <span className="block truncate sm:max-w-56">{p.filename}</span>
            <time dateTime={p.uploaded_at} className="tabular">
              {formatTimestamp(p.uploaded_at)}
            </time>
          </p>
        </li>
      ))}
    </ul>
  );
}
