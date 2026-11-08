import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { DEPTH_LABELS, DEPTHS, type Depth, type PaperDetail } from "@/lib/types";

import { DEPTH_STYLE } from "./DepthChip";

const READER: Record<Depth, { who: string; traits: string[] }> = {
  plain: { who: "For anyone curious", traits: ["No jargon", "One everyday comparison"] },
  student: { who: "For students", traits: ["Key terms defined", "How it works"] },
  expert: { who: "For practitioners", traits: ["Method and setup", "Reported numbers"] },
};

/** The opening of an explanation: its first sentence, or two when the first is short. */
export function opening(markdown: string, minLength = 90, maxLength = 230): string {
  const text = markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\$\$[\s\S]*?\$\$/g, " ")
    .replace(/^#+\s.*$/gm, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_`>#]/g, "")
    .replace(/^\s*[-+]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
  const sentences = text.match(/[^.!?]+[.!?]+(?=\s|$)/g) ?? [text];
  let result = "";
  for (const sentence of sentences) {
    if (result.length >= minLength) break;
    if (result && result.length + sentence.length > maxLength) break;
    result += sentence;
  }
  return result.trim() || text.slice(0, maxLength);
}

/** The same paper, opened three ways: how each depth begins, side by side. */
export function ThreeReaders({ paper }: { paper: PaperDetail }) {
  return (
    <div>
      <p className="max-w-[60ch] text-lg leading-relaxed">
        Every paper is written up three times. Here is how each version of <strong>{paper.title}</strong> begins.
      </p>
      <ol className="mt-8 grid gap-5 md:grid-cols-3">
        {DEPTHS.map((depth, i) => {
          const text = paper.explanations[depth];
          if (!text) return null;
          return (
            <li key={depth} className="flex flex-col border border-rule">
              <div className={`flex items-baseline justify-between gap-3 px-5 py-4 ${DEPTH_STYLE[depth]}`}>
                <h3 className="signage text-2xl font-extrabold">{DEPTH_LABELS[depth]}</h3>
                <span className="text-sm font-semibold">{READER[depth].who}</span>
              </div>
              <div className="flex items-center gap-1.5 px-5 pt-4" aria-hidden>
                {DEPTHS.map((_, level) => (
                  <span key={level} className={`h-1.5 flex-1 rounded-full ${level <= i ? "bg-band" : "bg-rule"}`} />
                ))}
              </div>
              <blockquote className="flex-1 px-5 pt-4 text-[1.0625rem] leading-relaxed">{opening(text)}</blockquote>
              <ul className="flex flex-wrap gap-1.5 px-5 pt-4" aria-label="What this version does">
                {READER[depth].traits.map((trait) => (
                  <li key={trait} className="rounded-[10px] border border-rule-strong px-2 py-0.5 text-[0.8125rem] font-semibold">
                    {trait}
                  </li>
                ))}
              </ul>
              <Link
                href={`/papers/${paper.id}?depth=${depth}` as never}
                className="mt-4 flex items-center justify-between gap-2 border-t border-rule px-5 py-3.5 font-semibold text-ink no-underline transition-colors duration-150 hover:bg-panel"
              >
                Read the {DEPTH_LABELS[depth]} version
                <ArrowRight className="size-4" aria-hidden />
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
