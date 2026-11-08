import { numberFormat } from "@/lib/format";

type Stop = { name: string; detail: string };

/** How an edition is made, drawn as a single-line strip map like the one above a train door. */
export function PipelineStrip({ scanned, changes, lines }: { scanned: number; changes: number; lines: number }) {
  const stops: Stop[] = [
    { name: "Scan", detail: `${numberFormat.format(scanned)} new arXiv papers in AI, learning, language and vision` },
    { name: "Pick", detail: `The ${changes} that change the field most, ranked` },
    { name: "Explain", detail: "What changed, what it builds on, and three depths of explanation" },
    { name: "Map", detail: `Placed on ${lines} research lines, with interchanges where fields meet` },
  ];
  return (
    <ol className="relative grid gap-8 md:grid-cols-4 md:gap-6">
      <span aria-hidden className="livery-y absolute bottom-3 left-[0.6rem] top-3 w-2.5 md:hidden" />
      <span aria-hidden className="livery-x absolute inset-x-3 top-[0.6rem] hidden h-2.5 md:block" />
      {stops.map((stop) => (
        <li key={stop.name} className="relative grid grid-cols-[2rem_1fr] content-start gap-3 md:grid-cols-1 md:gap-4">
          <span aria-hidden className="relative z-10 size-8 rounded-full border-[4px] border-band bg-white" />
          <div>
            <h3 className="signage text-xl font-bold">{stop.name}</h3>
            <p className="mt-1 max-w-[32ch] leading-relaxed text-ink-soft">{stop.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
