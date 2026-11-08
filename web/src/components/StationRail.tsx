"use client";

import { useEffect, useState } from "react";

import { LINES, type LineId, stationName } from "@/lib/lines";

type RailStation = { rank: number; title: string; lines: LineId[] };

/**
 * A sticky strip map beside the list of changes: every station in order, coloured by line,
 * with the one being read marked. Links jump to that station's entry.
 */
export function StationRail({ stations }: { stations: RailStation[] }) {
  const [current, setCurrent] = useState(stations[0]?.rank ?? 1);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (records) => {
        const visible = records.filter((r) => r.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setCurrent(Number((visible[0].target as HTMLElement).dataset.rank));
      },
      { rootMargin: "-20% 0px -60% 0px" },
    );
    stations.forEach((s) => {
      const el = document.getElementById(`station-${s.rank}`);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [stations]);

  return (
    <nav aria-label="Stations in this edition" className="sticky top-6">
      <h3 className="text-sm font-bold">Stations</h3>
      <ol className="mt-3">
        {stations.map((s, i) => {
          const line = LINES[s.lines[0]];
          const active = s.rank === current;
          return (
            <li key={s.rank} className="grid grid-cols-[1.5rem_1fr] gap-3">
              <div className="relative flex justify-center" aria-hidden>
                <span
                  className="absolute inset-y-0 w-1.5"
                  style={{ background: line.color, top: i === 0 ? "0.65rem" : 0, bottom: i === stations.length - 1 ? "calc(100% - 0.65rem)" : 0 }}
                />
                <span
                  className={`relative mt-1 w-3.5 border-[2.5px] border-ink bg-white ${s.lines.length > 1 ? "h-6 rounded-[7px]" : "h-3.5 rounded-full"} ${
                    active ? "outline outline-[3px] outline-signal" : ""
                  }`}
                />
              </div>
              <a
                href={`#station-${s.rank}`}
                aria-current={active ? "location" : undefined}
                className={`signage block pb-3 text-[0.9375rem] leading-snug no-underline ${active ? "font-bold text-ink" : "font-semibold text-ink-soft hover:text-ink"}`}
              >
                {stationName(s.title)}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
