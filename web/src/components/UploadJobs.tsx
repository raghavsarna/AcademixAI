"use client";

import { AlertTriangle, ArrowRight, Check, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { ACTIVE_JOB, type UploadJob, type UploadJobStatus } from "@/lib/types";

const STOPS = ["Sent", "Reading the PDF", "Writing the explanations", "Ready"];

// The stop each status has reached
const REACHED: Record<UploadJobStatus, number> = { queued: 1, reading: 1, analysing: 2, ready: 3, failed: 0 };

const NOW_DOING: Partial<Record<UploadJobStatus, string>> = {
  queued: "Waiting to start",
  reading: "Reading the PDF",
  analysing: "Writing what changed and the Plain, Student and Expert versions",
};

function elapsed(from: string, now: number): string {
  const seconds = Math.max(0, Math.round((now - new Date(from).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function ago(from: string, now: number): string {
  const minutes = Math.round((now - new Date(from).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `${hours} h ago` : new Date(from).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/** A ticking clock, only while something is running. */
function useNow(running: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [running]);
  return now;
}

/** The reader's uploads and how far each one has got. */
export function UploadJobs({
  jobs,
  onRetry,
  onDismiss,
}: {
  jobs: UploadJob[];
  onRetry: (id: string) => Promise<void>;
  onDismiss: (id: string) => Promise<void>;
}) {
  const now = useNow(jobs.some((j) => ACTIVE_JOB.includes(j.status)));
  return (
    <ul className="grid grid-cols-1 gap-4" aria-label="Your uploads">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} now={now} onRetry={onRetry} onDismiss={onDismiss} />
      ))}
    </ul>
  );
}

function JobCard({
  job,
  now,
  onRetry,
  onDismiss,
}: {
  job: UploadJob;
  now: number;
  onRetry: (id: string) => Promise<void>;
  onDismiss: (id: string) => Promise<void>;
}) {
  const [pending, setPending] = useState<"retry" | "dismiss" | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const active = ACTIVE_JOB.includes(job.status);

  async function act(kind: "retry" | "dismiss") {
    setPending(kind);
    setProblem(null);
    try {
      await (kind === "retry" ? onRetry(job.id) : onDismiss(job.id));
    } catch {
      setProblem(kind === "retry" ? "Couldn't start it again. Try once more." : "Couldn't remove it. Try once more.");
    } finally {
      setPending(null);
    }
  }

  const accent = job.status === "failed" ? "border-danger" : job.status === "ready" ? "border-line-learning" : "border-signal";
  return (
    <li className={`border border-l-[6px] border-rule bg-ground p-5 ${accent}`}>
      <div className="flex items-baseline justify-between gap-4">
        <p className="min-w-0 truncate font-bold" title={job.filename}>
          {job.status === "ready" && job.paper_title ? job.paper_title : job.filename}
        </p>
        <span className="tabular shrink-0 text-sm text-ink-soft">
          {active ? elapsed(job.created_at, now) : ago(job.updated_at, now)}
        </span>
      </div>

      {job.status === "failed" ? (
        <div className="mt-3">
          <p className="flex items-start gap-2 font-semibold text-danger" role="status">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
            {job.error ?? "This upload couldn't be explained."}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => act("retry")}
              disabled={pending !== null}
              className="inline-flex items-center gap-2 rounded-[4px] bg-band px-4 py-2 font-semibold text-white hover:bg-ink disabled:opacity-50"
            >
              <RotateCcw className="size-4" aria-hidden />
              {pending === "retry" ? "Starting…" : "Try again"}
            </button>
            <DismissButton pending={pending} onClick={() => act("dismiss")} />
          </div>
        </div>
      ) : (
        <>
          <Track reached={REACHED[job.status]} done={job.status === "ready"} />
          {active ? (
            <p className="mt-3 text-[0.9375rem] text-ink-soft" role="status">
              {NOW_DOING[job.status]}. This usually takes 10 to 40 seconds; you can leave this page.
            </p>
          ) : (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Link
                href={(job.url ?? "/library") as never}
                className="inline-flex items-center gap-2 rounded-[4px] bg-band px-4 py-2 font-semibold text-white no-underline hover:bg-ink"
              >
                Open the paper <ArrowRight className="size-4" aria-hidden />
              </Link>
              <DismissButton pending={pending} onClick={() => act("dismiss")} />
            </div>
          )}
        </>
      )}
      {problem ? (
        <p className="mt-2 text-sm font-semibold text-danger" role="alert">
          {problem}
        </p>
      ) : null}
    </li>
  );
}

function DismissButton({ pending, onClick }: { pending: string | null; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={pending !== null}
      className="rounded-[4px] px-3 py-2 font-semibold text-ink-soft hover:bg-panel hover:text-ink disabled:opacity-50"
    >
      {pending === "dismiss" ? "Removing…" : "Remove"}
    </button>
  );
}

/** The job's progress as a short strip map: stops passed are filled, the current one is lit. */
function Track({ reached, done }: { reached: number; done: boolean }) {
  return (
    <ol className="mt-4 grid grid-cols-4" aria-label="Progress">
      {STOPS.map((stop, i) => {
        const passed = i < reached || done;
        const current = i === reached && !done;
        return (
          <li key={stop} className="relative flex flex-col items-start gap-2" aria-current={current ? "step" : undefined}>
            {i < STOPS.length - 1 ? (
              <span aria-hidden className={`absolute left-3 right-0 top-[0.6rem] h-1.5 ${i < reached ? "bg-band" : "bg-rule"}`} />
            ) : null}
            <span
              aria-hidden
              className={`relative z-10 grid size-6 place-items-center rounded-full border-[3px] ${
                passed ? "border-band bg-band text-white" : current ? "border-band bg-signal" : "border-rule-strong bg-white"
              } ${current ? "motion-safe:animate-pulse" : ""}`}
            >
              {passed ? <Check className="size-3.5" strokeWidth={3.5} /> : null}
            </span>
            <span className={`pr-2 text-[0.8125rem] leading-tight ${current ? "font-bold text-ink" : passed ? "font-semibold" : "text-ink-soft"}`}>
              {stop}
              <span className="sr-only">{passed ? " (done)" : current ? " (in progress)" : ""}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
