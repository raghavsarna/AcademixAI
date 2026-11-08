"use client";

import { api } from "@/lib/client-api";
import { useDepth } from "@/lib/use-depth";

import { ChatPanel } from "./ChatPanel";
import { DepthSwitch } from "./DepthSwitch";

export function EditionChat({ date, path }: { date: string; path: string }) {
  const [depth, setDepth] = useDepth();
  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-prose text-ink-soft">
          Not sure what a change means for you? Ask about this edition and pick how deep the answer goes.
        </p>
        <DepthSwitch value={depth} onChange={setDepth} label="Answer depth" />
      </div>
      <ChatPanel
        title="Ask about this edition"
        depth={depth}
        ask={(message, level) => api.askEdition(date, message, level)}
        suggestions={["What was the biggest change?", "Which paper matters most for students?", "Explain the themes simply"]}
        returnTo={path}
      />
    </div>
  );
}
