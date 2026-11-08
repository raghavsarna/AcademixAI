"use client";

import { api } from "@/lib/client-api";
import { type Depth, DEPTH_LABELS, type PaperDetail } from "@/lib/types";
import { useDepth } from "@/lib/use-depth";

import { ChatPanel } from "./ChatPanel";
import { DepthSwitch } from "./DepthSwitch";
import { Markdown } from "./Markdown";
import { SignBand } from "./SignBand";

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
        <SignBand title="Explained at your level" id="explanation-title">
          <DepthSwitch value={depth} onChange={setDepth} controls="explanation" tone="dark" />
        </SignBand>
        <p className="mt-4 font-semibold text-ink-soft">{AUDIENCE[depth]}</p>
        <div
          id="explanation"
          role="tabpanel"
          aria-label={`${DEPTH_LABELS[depth]} explanation`}
          key={depth}
          className="depth-settle mt-4"
        >
          <Markdown>{text}</Markdown>
        </div>
      </section>

      <ChatPanel
        title="Ask about this paper"
        depth={depth}
        ask={(message, level) => api.askPaper(paper.id, message, level)}
        stream={(message, level, handlers) => api.streamPaperAnswer(paper.id, message, level, handlers)}
        suggestions={["What problem does it solve?", "What are the limitations?", "How could I use this?"]}
        returnTo={`/papers/${paper.id}`}
      />
    </div>
  );
}
