"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";

import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/client-api";
import { DEPTH_LABELS, type Depth } from "@/lib/types";

import { Markdown } from "./Markdown";
import { SignBand } from "./SignBand";

type Message = { role: "you" | "academixai"; text: string; depth: Depth };

export function ChatPanel({
  title,
  depth,
  ask,
  suggestions,
  returnTo,
}: {
  title: string;
  depth: Depth;
  ask: (message: string, depth: Depth) => Promise<{ reply: string }>;
  suggestions: string[];
  returnTo: string;
}) {
  const { status } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();
  const listRef = useRef<HTMLOListElement>(null);

  async function send(text: string) {
    const question = text.trim();
    if (!question || pending) return;
    setError(null);
    setPending(true);
    setMessages((m) => [...m, { role: "you", text: question, depth }]);
    setDraft("");
    try {
      const { reply } = await ask(question, depth);
      setMessages((m) => [...m, { role: "academixai", text: reply, depth }]);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach AcademixAI. Check your connection and try again.");
      setDraft(question);
      setMessages((m) => m.slice(0, -1));
    } finally {
      setPending(false);
      requestAnimationFrame(() => listRef.current?.lastElementChild?.scrollIntoView({ block: "nearest" }));
    }
  }

  return (
    <section aria-labelledby={`${inputId}-title`} className="border border-t-0 border-rule">
      <SignBand title={title} id={`${inputId}-title`}>
        <p className="text-sm text-band-soft">
          Answers at <strong className="text-white">{DEPTH_LABELS[depth]}</strong> depth
        </p>
      </SignBand>

      {status === "signed-out" ? (
        <div className="px-5 pb-6 pt-5">
          <p className="max-w-prose leading-relaxed">
            Ask anything about it and get an answer at your depth. Chat needs a free account so it can be kept fair
            for everyone.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href={`/signup?next=${encodeURIComponent(returnTo)}` as never}
              className="rounded-[4px] bg-band px-4 py-2.5 font-semibold text-white no-underline hover:bg-ink"
            >
              Create an account
            </Link>
            <Link
              href={`/login?next=${encodeURIComponent(returnTo)}` as never}
              className="rounded-[4px] border border-rule-strong px-4 py-2.5 font-semibold text-ink no-underline hover:border-ink"
            >
              Log in
            </Link>
          </div>
        </div>
      ) : (
        <div className="px-5 pb-5 pt-5">
          {messages.length ? (
            <ol ref={listRef} className="grid max-h-[28rem] gap-4 overflow-y-auto pr-1" aria-live="polite">
              {messages.map((m, i) => (
                <li key={i} className={m.role === "you" ? "justify-self-end" : ""}>
                  {m.role === "you" ? (
                    <p className="max-w-[46ch] rounded-[4px] bg-band px-4 py-2.5 text-white">{m.text}</p>
                  ) : (
                    <div className="max-w-[60ch] rounded-[4px] border border-rule bg-ground px-4 py-3">
                      <Markdown className="prose-column text-base">{m.text}</Markdown>
                    </div>
                  )}
                </li>
              ))}
            </ol>
          ) : (
            <ul className="flex flex-wrap gap-2" aria-label="Suggested questions">
              {suggestions.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    onClick={() => send(s)}
                    disabled={pending || status !== "signed-in"}
                    className="rounded-full border border-rule-strong bg-ground px-3.5 py-1.5 text-sm font-semibold transition-colors duration-150 hover:border-ink disabled:opacity-50"
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          )}

          {pending ? (
            <p className="mt-4 text-sm font-semibold text-ink-soft" role="status">
              Working out an answer at {DEPTH_LABELS[depth]} depth&hellip;
            </p>
          ) : null}
          {error ? (
            <p className="mt-4 text-sm font-semibold text-danger" role="alert">
              {error}
            </p>
          ) : null}

          <form
            className="mt-4 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(draft);
            }}
          >
            <label htmlFor={inputId} className="sr-only">
              Your question
            </label>
            <input
              id={inputId}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              maxLength={2000}
              placeholder="Ask a question about it"
              disabled={status !== "signed-in"}
              className="min-w-0 flex-1 rounded-[4px] border border-rule-strong bg-ground px-3.5 py-2.5 placeholder:text-ink-soft focus-visible:border-link disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={pending || !draft.trim() || status !== "signed-in"}
              className="rounded-[4px] bg-band px-5 py-2.5 font-semibold text-white transition-colors duration-150 hover:bg-ink disabled:cursor-not-allowed disabled:opacity-50"
            >
              Ask
            </button>
          </form>
        </div>
      )}
    </section>
  );
}
