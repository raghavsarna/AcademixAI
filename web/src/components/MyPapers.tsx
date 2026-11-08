"use client";

import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { api, ApiError } from "@/lib/client-api";
import { formatTimestamp } from "@/lib/format";
import type { MyPaper } from "@/lib/types";
import { useUploadJobs } from "@/lib/use-upload-jobs";

import { ListSkeleton } from "./Skeletons";
import { UploadJobs } from "./UploadJobs";

export function MyPapers() {
  const [papers, setPapers] = useState<MyPaper[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const uploads = useUploadJobs(true);
  const unfinished = uploads.jobs?.filter((j) => j.status !== "ready") ?? [];
  const finishedCount = uploads.jobs?.filter((j) => j.status === "ready").length ?? 0;

  // Reload the list whenever another upload finishes
  useEffect(() => {
    api
      .myPapers()
      .then(setPapers)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load your papers. Try again."));
  }, [finishedCount]);

  async function remove(paper: MyPaper) {
    await api.deletePaper(paper.id);
    setPapers((current) => (current ?? []).filter((p) => p.id !== paper.id));
    setAnnouncement(`Deleted ${paper.title}.`);
    uploads.refresh();
  }

  const inProgress = unfinished.length ? (
    <section aria-labelledby="unfinished-title" className="mb-10 max-w-2xl">
      <h2 id="unfinished-title" className="mb-4 text-xl font-bold">
        Still being explained
      </h2>
      <UploadJobs jobs={unfinished} onRetry={uploads.retry} onDismiss={uploads.dismiss} />
    </section>
  ) : null;

  const status = (
    <p className="sr-only" role="status">
      {announcement}
    </p>
  );

  if (error) {
    return (
      <p className="font-semibold text-danger" role="alert">
        {error}
      </p>
    );
  }
  if (!papers) return <ListSkeleton />;

  if (!papers.length) {
    return (
      <>
        {status}
        {inProgress}
        <div className="max-w-2xl border border-rule p-6">
          <h2 className="text-xl font-bold">No papers yet</h2>
          <p className="mt-2 leading-relaxed text-ink-soft">
            Upload a PDF and it shows up here with what it changes and its three explanations, ready to come back to.
          </p>
          <Link href="/explain" className="mt-4 inline-block font-semibold text-link underline">
            Explain your first paper
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      {status}
      {inProgress}
      <ul className="border-b border-rule">
        {papers.map((p) => (
          <PaperRow key={p.id} paper={p} onDelete={() => remove(p)} />
        ))}
      </ul>
    </>
  );
}

function PaperRow({ paper, onDelete }: { paper: MyPaper; onDelete: () => Promise<void> }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  // Put the keyboard on the safe choice when the confirmation opens
  useEffect(() => {
    if (confirming) cancel.current?.focus();
  }, [confirming]);

  function close() {
    setConfirming(false);
    setProblem(null);
    requestAnimationFrame(() => trigger.current?.focus());
  }

  async function confirm() {
    setDeleting(true);
    setProblem(null);
    try {
      await onDelete();
    } catch (e) {
      setProblem(e instanceof ApiError ? e.message : "Couldn't delete it. Try again.");
      setDeleting(false);
    }
  }

  return (
    <li className="border-t border-rule py-5">
      <div className="grid gap-x-6 gap-y-2 sm:grid-cols-[1fr_auto]">
        <div className="min-w-0">
          <Link href={`/papers/${paper.id}`} className="text-lg font-bold text-ink no-underline hover:underline">
            {paper.title}
          </Link>
          {paper.what_changed ? (
            <p className="mt-1 max-w-[80ch] leading-relaxed text-ink-soft">{paper.what_changed}</p>
          ) : null}
        </div>
        <div className="flex items-start justify-between gap-4 sm:flex-col sm:items-end">
          <p className="text-sm text-ink-soft sm:text-right">
            <span className="block truncate sm:max-w-56">{paper.filename}</span>
            <time dateTime={paper.uploaded_at} className="tabular">
              {formatTimestamp(paper.uploaded_at)}
            </time>
          </p>
          {confirming ? null : (
            <button
              ref={trigger}
              type="button"
              onClick={() => setConfirming(true)}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-[4px] px-2 py-1.5 text-sm font-semibold text-ink-soft transition-colors duration-150 hover:bg-panel hover:text-danger"
              aria-label={`Delete ${paper.title}`}
            >
              <Trash2 className="size-4" aria-hidden />
              Delete
            </button>
          )}
        </div>
      </div>

      {confirming ? (
        <div
          role="group"
          aria-label={`Confirm deleting ${paper.title}`}
          className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-3 border-l-[6px] border-danger bg-panel px-4 py-3"
          onKeyDown={(e) => {
            if (e.key === "Escape" && !deleting) close();
          }}
        >
          <p className="min-w-0 flex-1 basis-64 text-[0.9375rem] leading-relaxed">
            <strong>Delete this paper from your papers?</strong> The PDF you uploaded is deleted too. This can&rsquo;t
            be undone.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={confirm}
              disabled={deleting}
              className="rounded-[4px] bg-danger px-4 py-2 font-semibold text-white transition-colors duration-150 hover:opacity-90 disabled:opacity-60"
            >
              {deleting ? "Deleting…" : "Delete"}
            </button>
            <button
              ref={cancel}
              type="button"
              onClick={close}
              disabled={deleting}
              className="rounded-[4px] border border-rule-strong bg-ground px-4 py-2 font-semibold hover:border-ink disabled:opacity-60"
            >
              Cancel
            </button>
          </div>
          {problem ? (
            <p className="w-full text-sm font-semibold text-danger" role="alert">
              {problem}
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
