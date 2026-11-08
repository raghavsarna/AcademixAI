"use client";

import { FileText, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";

import { api, ApiError } from "@/lib/client-api";

const MAX_MB = 20;

const STAGES = [
  "Uploading the PDF",
  "Reading the paper",
  "Working out what changed",
  "Writing the Plain, Student and Expert versions",
];

function sizeLabel(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function problemWith(file: File): string | null {
  if (!(file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"))) return "That file isn't a PDF.";
  if (file.size > MAX_MB * 1024 * 1024) return `That PDF is ${sizeLabel(file.size)}. The limit is ${MAX_MB} MB.`;
  if (file.size === 0) return "That file is empty.";
  return null;
}

export function UploadForm() {
  const router = useRouter();
  const inputId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 4500);
    return () => window.clearInterval(timer);
  }, [busy]);

  function choose(next: File | undefined) {
    if (!next) return;
    const problem = problemWith(next);
    setError(problem);
    setFile(problem ? null : next);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || busy) return;
    setStage(0);
    setBusy(true);
    setError(null);
    try {
      const result = await api.upload(file);
      router.push(result.url as never);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The upload didn't go through. Check your connection and try again.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-8 max-w-2xl" aria-busy={busy}>
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
        className={`flex cursor-pointer flex-col items-center gap-3 rounded-[6px] border-[2.5px] border-dashed px-6 py-12 text-center transition-colors duration-150 ${
          dragging ? "border-link bg-[#e8f0fc]" : "border-rule-strong bg-panel hover:border-ink"
        } ${busy ? "pointer-events-none opacity-60" : ""}`}
      >
        <Upload className="size-8" aria-hidden strokeWidth={2} />
        <span className="text-lg font-bold">Drop a PDF here, or choose one</span>
        <span className="text-sm text-ink-soft">One research paper, up to {MAX_MB} MB. Scanned PDFs without text can&rsquo;t be read yet.</span>
        <input
          id={inputId}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          disabled={busy}
          onChange={(e) => choose(e.target.files?.[0])}
        />
      </label>

      {file ? (
        <p className="mt-4 flex items-center gap-2 font-semibold">
          <FileText className="size-5 shrink-0" aria-hidden />
          <span className="truncate">{file.name}</span>
          <span className="shrink-0 font-normal text-ink-soft">{sizeLabel(file.size)}</span>
        </p>
      ) : null}

      {error ? (
        <p className="mt-4 font-semibold text-danger" role="alert">
          {error}
        </p>
      ) : null}

      {busy ? (
        <div className="mt-6" role="status" aria-live="polite">
          <ol className="grid gap-2">
            {STAGES.map((label, i) => (
              <li key={label} className={`flex items-center gap-3 ${i <= stage ? "text-ink" : "text-ink-soft"}`}>
                <span
                  aria-hidden
                  className={`size-4 shrink-0 rounded-full border-[3px] ${
                    i < stage ? "border-band bg-band" : i === stage ? "border-band bg-signal" : "border-rule-strong bg-white"
                  }`}
                />
                <span className={i === stage ? "font-bold" : ""}>{label}</span>
              </li>
            ))}
          </ol>
          <p className="mt-3 text-sm text-ink-soft">This usually takes 10 to 40 seconds.</p>
        </div>
      ) : null}

      <button
        type="submit"
        disabled={!file || busy}
        className="mt-6 rounded-[4px] bg-band px-6 py-3 text-lg font-bold text-white transition-colors duration-150 hover:bg-ink disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Explaining…" : "Explain this paper"}
      </button>
    </form>
  );
}
