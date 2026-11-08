import { DepthChip } from "./DepthChip";
import { SignBand } from "./SignBand";

type Stop = { name: string; detail: string; sample?: React.ReactNode };

const STOPS: Stop[] = [
  {
    name: "What changed",
    detail: "One or two sentences on what the paper claims is new, and the kind of change it is.",
  },
  {
    name: "What it builds on",
    detail: "The earlier work it extends, replaces or challenges, as named in the paper.",
    sample: (
      <span className="inline-flex flex-wrap gap-1.5 text-[0.8125rem]">
        <span className="rounded-[10px] border-2 border-ink px-2 py-0.5">
          <span className="text-ink-soft">Replaces</span> <strong>RNNs</strong>
        </span>
        <span className="rounded-[10px] border-2 border-ink px-2 py-0.5">
          <span className="text-ink-soft">Extends</span> <strong>Encoder-decoders</strong>
        </span>
      </span>
    ),
  },
  {
    name: "Three depths",
    detail: "The whole paper explained three times, for three kinds of reader.",
    sample: (
      <span className="inline-flex flex-wrap gap-1.5">
        <DepthChip depth="plain" />
        <DepthChip depth="student" />
        <DepthChip depth="expert" />
      </span>
    ),
  },
  {
    name: "A chat at your depth",
    detail: "Ask follow-up questions about the paper. Answers match the depth you are reading at.",
  },
];

/** What an upload turns into, drawn as the stops along one line. */
export function WhatYouGet() {
  return (
    <section aria-labelledby="what-you-get">
      <SignBand title="What you get back" id="what-you-get" bleed={false} />
      <ol className="border border-t-0 border-rule px-5 pb-2 pt-6 sm:px-8">
        {STOPS.map((stop, i) => (
          <li key={stop.name} className="grid grid-cols-[1.75rem_1fr] gap-4">
            <div className="relative flex justify-center" aria-hidden>
              {i < STOPS.length - 1 ? <span className="absolute inset-y-0 top-3 w-2 bg-band" /> : null}
              <span className="relative mt-0.5 size-6 rounded-full border-[4px] border-band bg-signal" />
            </div>
            <div className="pb-6">
              <h3 className="signage text-lg font-bold">{stop.name}</h3>
              <p className="mt-1 max-w-[46ch] leading-relaxed text-ink-soft">{stop.detail}</p>
              {stop.sample ? <div className="mt-2.5">{stop.sample}</div> : null}
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-sm text-ink-soft">
        Your uploads are private to you. A paper&rsquo;s page can be shared by its link.
      </p>
    </section>
  );
}
