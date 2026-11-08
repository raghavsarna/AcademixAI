"use client";

import Link from "next/link";
import { useState } from "react";

import { type Depth, DEPTH_LABELS, type PaperDetail } from "@/lib/types";

import { DepthSwitch } from "./DepthSwitch";
import { Markdown } from "./Markdown";

const READER: Record<Depth, string> = {
  plain: "for someone who has never read a paper",
  student: "for a student meeting the idea for the first time",
  expert: "for a practitioner who wants the method and numbers",
};

/** One real paper, switchable between the three depths right on the landing page. */
export function DepthDemo({ paper }: { paper: PaperDetail }) {
  const [depth, setDepth] = useState<Depth>("plain");
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:gap-14">
      <div>
        <p className="text-lg leading-relaxed">
          Every paper is written up three times. Switch the depth and the same idea is rewritten{" "}
          <strong>{READER[depth]}</strong>.
        </p>
        <div className="mt-6">
          <DepthSwitch value={depth} onChange={setDepth} label="Try a depth" controls="demo-explanation" />
        </div>
        <Link href={`/papers/${paper.id}?depth=${depth}` as never} className="mt-6 inline-block font-semibold text-link underline">
          Open the full page for this paper
        </Link>
      </div>
      <div className="border border-rule p-5 sm:p-8">
        <h3 className="text-xl font-bold leading-snug">{paper.title}</h3>
        <p className="mt-1 text-sm font-semibold text-ink-soft">{DEPTH_LABELS[depth]} explanation</p>
        <div id="demo-explanation" role="tabpanel" aria-label={`${DEPTH_LABELS[depth]} explanation`} key={depth} className="depth-settle mt-4">
          <Markdown>{paper.explanations[depth] ?? ""}</Markdown>
        </div>
      </div>
    </div>
  );
}
