import type { BuildsOn } from "@/lib/types";

const RELATION_LABELS: Record<string, string> = {
  extends: "Extends",
  challenges: "Challenges",
  "compares-with": "Compares with",
  applies: "Applies",
  replaces: "Replaces",
};

/** Earlier work a paper connects to, set as interchange signs. */
export function Transfers({ items }: { items: BuildsOn[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
      <span className="font-bold">Transfers</span>
      {items.map((b) => (
        <span key={b.work} className="inline-flex max-w-full flex-wrap items-baseline gap-x-1.5 rounded-[10px] border-[2.5px] border-ink bg-ground px-3 py-1 leading-snug">
          <span className="text-ink-soft">{RELATION_LABELS[b.relation] ?? "Extends"}</span>
          <span className="font-semibold">{b.work}</span>
        </span>
      ))}
    </div>
  );
}
