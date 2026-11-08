"use client";

import { api } from "@/lib/client-api";
import { type Depth, DEPTH_LABELS, type PaperDetail } from "@/lib/types";
import { useDepth } from "@/lib/use-depth";

import { ChatPanel } from "./ChatPanel";
import { DepthSwitch } from "./DepthSwitch";
import { Markdown } from "./Markdown";

const AUDIENCE: Record<Depth, string> = {
  plain: "For anyone: no jargon, one everyday comparison.",
  student: "For students: key terms defined as they come up.",
  expert: "For practitioners: method, setup and reported numbers.",
};

/** The explanation at the reader's depth, plus chat that answers at the same depth. */
export function PaperReader({ paper }: { paper: PaperDetail }) {
  const [depth, setDepth] = useDepth();
  const text = paper.explanations[depth] ?? paper.explanations.student ?? paper.abstract ?? "";

  return (
    <div className="grid gap-10">
      <section aria-labelledby="explanation-title">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="explanation-title" className="text-2xl font-bold">
              Explained at your level
            </h2>
            <p className="mt-1 text-ink-soft">{AUDIENCE[depth]}</p>
          </div>
          <DepthSwitch value={depth} onChange={setDepth} controls="explanation" />
        </div>
        <div
          id="explanation"
          role="tabpanel"
          aria-label={`${DEPTH_LABELS[depth]} explanation`}
          key={depth}
          className="depth-settle mt-6"
        >
          <Markdown>{text}</Markdown>
        </div>
      </section>

      <ChatPanel
        title="Ask about this paper"
        depth={depth}
        ask={(message, level) => api.askPaper(paper.id, message, level)}
        suggestions={["What problem does it solve?", "What are the limitations?", "How could I use this?"]}
        returnTo={`/papers/${paper.id}`}
      />
    </div>
  );
}
