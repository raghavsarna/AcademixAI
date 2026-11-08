"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";

import { useAuth } from "@/lib/auth";
import { ApiError, type StreamHandlers } from "@/lib/client-api";
import { type ChatAnswer, type ChatSource, DEPTH_LABELS, type Depth } from "@/lib/types";

import { Markdown } from "./Markdown";
import { SignBand } from "./SignBand";

type Message =
  | { role: "you"; text: string }
  | { role: "academixai"; text: string; depth: Depth; sources: ChatSource[]; streaming: boolean };

const CITATION = /\[(\d{1,2})\](?!\()/g;

/** House style: no em dashes, even when the model writes them (a stream can split one across pieces). */
function tidy(text: string): string {
  return text.replace(/\s*\u2014\s*/g, ", ");
}

/** The citation numbers an answer uses, in order. */
function cited(text: string): number[] {
  return [...new Set([...text.matchAll(CITATION)].map((m) => Number(m[1])))].sort((a, b) => a - b);
}

/** Turn [2] into a link to that answer's second source, so the reader can check the passage. */
function linkCitations(text: string, key: number, sources: ChatSource[]): string {
  const known = new Set(sources.map((s) => s.number));
  return text.replace(CITATION, (match, n) => (known.has(Number(n)) ? `[[${n}]](#cite-${key}-${n})` : match));
}

export function ChatPanel({
  title,
  depth,
  ask,
  stream,
  suggestions,
  returnTo,
}: {
  title: string;
  depth: Depth;
  ask: (message: string, depth: Depth) => Promise<ChatAnswer>;
  /** When given, answers are shown as they are written, with the passages they cite. */
  stream?: (message: string, depth: Depth, handlers: StreamHandlers) => Promise<void>;
  suggestions: string[];
  returnTo: string;
}) {
  const { status } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();
  const listRef = useRef<HTMLOListElement>(null);

  function updateAnswer(change: (m: Extract<Message, { role: "academixai" }>) => Partial<Message>) {
    setMessages((all) => {
      const last = all.at(-1);
      if (!last || last.role !== "academixai") return all;
      return [...all.slice(0, -1), { ...last, ...change(last) } as Message];
    });
  }

  function scrollToEnd() {
    requestAnimationFrame(() => listRef.current?.lastElementChild?.scrollIntoView({ block: "nearest" }));
  }

  async function send(text: string) {
    const question = text.trim();
    if (!question || pending) return;
    setError(null);
    setPending(true);
    setProgress(stream ? "Finding the passages that answer this" : null);
    setMessages((m) => [...m, { role: "you", text: question }]);
    setDraft("");
    scrollToEnd();
    let received = false;
    try {
      if (stream) {
        setMessages((m) => [...m, { role: "academixai", text: "", depth, sources: [], streaming: true }]);
        await stream(question, depth, {
          onStatus: (detail) => setProgress(detail.replace(/\.$/, "")),
          onSources: (sources) => {
            setProgress("Writing the answer");
            updateAnswer(() => ({ sources }));
          },
          onText: (piece) => {
            received = true;
            setProgress(null);
            updateAnswer((m) => ({ text: m.text + piece }));
          },
        });
        updateAnswer(() => ({ streaming: false }));
      } else {
        const { reply, sources } = await ask(question, depth);
        setMessages((m) => [...m, { role: "academixai", text: reply, depth, sources, streaming: false }]);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach AcademixAI. Check your connection and try again.");
      if (received) {
        // Keep the part of the answer that arrived
        updateAnswer(() => ({ streaming: false }));
      } else {
        // Nothing came back: take the question off the list and put it back in the box
        setMessages((all) => all.filter((m) => !(m.role === "academixai" && !m.text)).slice(0, -1));
        setDraft(question);
      }
    } finally {
      setPending(false);
      setProgress(null);
      scrollToEnd();
    }
  }

  // A citation opens its passage in the list under the answer
  function openCitation(event: React.MouseEvent) {
    const link = (event.target as HTMLElement).closest<HTMLAnchorElement>("a[data-cite]");
    if (!link) return;
    event.preventDefault();
    const source = document.getElementById(link.getAttribute("href")!.slice(1)) as HTMLDetailsElement | null;
    if (!source) return;
    source.open = true;
    source.scrollIntoView({ block: "nearest" });
    source.querySelector("summary")?.focus();
  }

  return (
    <section aria-labelledby={`${inputId}-title`} className="-mx-5 border-b border-rule sm:-mx-8 sm:border-x">
      <SignBand title={title} id={`${inputId}-title`} bleed={false}>
        <p className="text-sm text-band-soft">
          Answers at <strong className="text-white">{DEPTH_LABELS[depth]}</strong> depth
          {stream ? ", from the paper's full text" : ""}
        </p>
      </SignBand>

      {status === "signed-out" ? (
        <div className="px-5 pb-6 pt-5 sm:px-8">
          <p className="max-w-prose leading-relaxed">
            Ask anything about it and get an answer at your depth
            {stream ? ", with the passages of the paper it comes from" : ""}. Chat needs a free account so it can be
            kept fair for everyone.
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
        <div className="px-5 pb-5 pt-5 sm:px-8">
          {messages.length ? (
            <ol ref={listRef} className="grid max-h-[34rem] gap-4 overflow-y-auto pr-1" onClick={openCitation}>
              {messages.map((m, i) => (
                <li key={i} className={m.role === "you" ? "justify-self-end" : ""}>
                  {m.role === "you" ? (
                    <p className="max-w-[46ch] rounded-[4px] bg-band px-4 py-2.5 text-white">{m.text}</p>
                  ) : (
                    <Answer message={m} index={i} />
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

          <p className="mt-4 min-h-5 text-sm font-semibold text-ink-soft" role="status">
            {pending && (progress || !stream)
              ? `${progress ?? `Working out an answer at ${DEPTH_LABELS[depth]} depth`}…`
              : ""}
          </p>
          {error ? (
            <p className="mt-1 text-sm font-semibold text-danger" role="alert">
              {error}
            </p>
          ) : null}

          <form
            className="mt-3 flex gap-2"
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

function Answer({ message, index }: { message: Extract<Message, { role: "academixai" }>; index: number }) {
  const numbers = cited(message.text);
  const used = message.sources.filter((s) => numbers.includes(s.number));
  if (!message.text && message.streaming) return null;
  return (
    <div className="max-w-[62ch] rounded-[4px] border border-rule bg-ground px-4 py-3" aria-busy={message.streaming}>
      <Markdown className="prose-column text-base">{linkCitations(tidy(message.text), index, message.sources)}</Markdown>
      {message.streaming ? <span className="stream-caret" aria-hidden /> : null}
      {used.length ? (
        <div className="mt-3 border-t border-rule pt-3">
          <p className="text-sm font-bold">From the paper</p>
          <ol className="mt-1.5 grid gap-1">
            {used.map((s) => (
              <li key={s.number}>
                <details id={`cite-${index}-${s.number}`} className="group">
                  <summary className="cursor-pointer rounded-[3px] py-0.5 text-sm text-ink-soft marker:text-rule-strong hover:text-ink">
                    <span className="citation-chip">{s.number}</span> {s.section ?? "Opening"}
                    {s.page ? `, page ${s.page}` : ""}
                  </summary>
                  <blockquote className="my-2 border-l-4 border-signal pl-3 text-sm leading-relaxed text-ink-soft">
                    {s.text}
                  </blockquote>
                </details>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  );
}
