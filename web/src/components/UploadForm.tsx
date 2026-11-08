"use client";

import { FileText, Upload, X } from "lucide-react";
import { useId, useRef, useState } from "react";

import { api, ApiError } from "@/lib/client-api";
import type { UploadJob } from "@/lib/types";

const MAX_MB = 20;

function sizeLabel(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function problemWith(file: File): string | null {
  if (!(file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"))) return "That file isn't a PDF.";
  if (file.size > MAX_MB * 1024 * 1024) return `That PDF is ${sizeLabel(file.size)}. The limit is ${MAX_MB} MB.`;
  if (file.size === 0) return "That file is empty.";
  return null;
}

/**
 * Pick a PDF and send it. The form is only busy while the file is being sent: the server answers
 * at once with a job, which is handed to `onStarted`, and the form is ready for the next paper.
 */
export function UploadForm({ onStarted }: { onStarted: (job: UploadJob) => void }) {
  const inputId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  function choose(next: File | undefined) {
    if (!next) return;
    const problem = problemWith(next);
    setError(problem);
    setFile(problem ? null : next);
  }

  function clear() {
    setFile(null);
    if (input.current) input.current.value = "";
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || sending) return;
    setSending(true);
    setError(null);
    try {
      const job = await api.upload(file);
      clear();
      onStarted(job);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The upload didn't go through. Check your connection and try again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={submit} aria-busy={sending}>
      <label
        htmlFor={inputId}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          choose(e.dataTransfer.files[0]);
        }}
        className={`flex cursor-pointer flex-col items-center gap-3 rounded-[6px] border-[2.5px] border-dashed px-6 py-14 text-center transition-colors duration-150 ${
          dragging ? "border-ink bg-depth-plain" : "border-rule-strong bg-ground hover:border-ink hover:bg-panel"
        } ${sending ? "pointer-events-none opacity-60" : ""}`}
      >
        <span className="grid size-14 place-items-center rounded-full bg-signal" aria-hidden>
          <Upload className="size-7" strokeWidth={2.25} />
        </span>
        <span className="text-xl font-bold">Drop a PDF here, or choose one</span>
        <span className="max-w-[44ch] text-[0.9375rem] text-ink-soft">
          One research paper, up to {MAX_MB} MB. Scanned PDFs without a text layer can&rsquo;t be read yet.
        </span>
        <input
          ref={input}
          id={inputId}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          disabled={sending}
          onChange={(e) => choose(e.target.files?.[0])}
        />
      </label>

      {file ? (
        <div className="mt-4 flex items-center gap-3 border border-rule px-4 py-3">
          <FileText className="size-5 shrink-0" aria-hidden />
          <span className="min-w-0 flex-1 truncate font-semibold">{file.name}</span>
          <span className="tabular shrink-0 text-sm text-ink-soft">{sizeLabel(file.size)}</span>
          <button
            type="button"
            onClick={clear}
            disabled={sending}
            className="grid size-8 shrink-0 place-items-center rounded-[4px] text-ink-soft hover:bg-panel hover:text-ink"
            aria-label={`Remove ${file.name}`}
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>
      ) : null}

      {error ? (
        <p className="mt-4 font-semibold text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={!file || sending}
        className="mt-5 w-full rounded-[4px] bg-band px-6 py-3.5 text-lg font-bold text-white transition-colors duration-150 hover:bg-ink disabled:cursor-not-allowed disabled:opacity-45 sm:w-auto"
      >
        {sending ? "Sending the PDF…" : "Explain this paper"}
      </button>
    </form>
  );
}
