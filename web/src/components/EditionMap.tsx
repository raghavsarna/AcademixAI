"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { LINE_ORDER, LINES, type LineId, linesForPaper, stationName } from "@/lib/lines";
import { CHANGE_TYPE_LABELS, type PaperCard } from "@/lib/types";

import { LineBullets } from "./LineBullet";

type Entry = { rank: number; paper: PaperCard };

const W = 1000;
const LEFT = 172;
const RIGHT = 28;
const TOP = 40;
const GAP = 62;

type Station = {
  entry: Entry;
  lines: LineId[];
  x: number;
  ys: number[];
  y: number;
  yTo: number;
  name: string;
  labelAbove: boolean;
};

function layout(entries: Entry[]) {
  const used = new Set<LineId>();
  for (const e of entries) linesForPaper(e.paper.categories).slice(0, 2).forEach((l) => used.add(l));
  const lines = LINE_ORDER.filter((l) => used.has(l));
  const y = (line: LineId) => TOP + lines.indexOf(line) * GAP;
  const step = (W - LEFT - RIGHT) / Math.max(entries.length, 1);
  const stations: Station[] = entries.map((entry, i) => {
    const own = linesForPaper(entry.paper.categories).slice(0, 2);
    const ys = own.map(y);
    return {
      entry,
      lines: own,
      x: LEFT + step * (i + 0.5),
      ys,
      y: Math.min(...ys),
      yTo: Math.max(...ys),
      name: stationName(entry.paper.title, 20),
      labelAbove: i % 2 === 0,
    };
  });
  const height = TOP + (lines.length - 1) * GAP + 40;
  return { lines, y, stations, height };
}

export function EditionMap({ entries, editionLabel }: { entries: Entry[]; editionLabel: string }) {
  const { lines, y, stations, height } = useMemo(() => layout(entries), [entries]);
  const [selected, setSelected] = useState(0);
  const current = stations[selected] ?? stations[0];

  if (!stations.length) return null;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,2.1fr)_minmax(19rem,1fr)] lg:items-start">
      {/* Diagram: wide screens */}
      <figure className="hidden md:block">
        <svg
          viewBox={`0 0 ${W} ${height}`}
          className="w-full overflow-visible"
          role="group"
          aria-label={`Line diagram of ${editionLabel}: ${stations.length} papers on ${lines.length} research lines`}
        >
          {lines.map((line, i) => {
            const len = W - RIGHT - (LEFT - 18);
            return (
              <g key={line}>
                <text x={0} y={y(line) + 5} className="signage fill-ink text-[16px] font-bold">
                  {LINES[line].name}
                </text>
                <path
                  d={`M ${LEFT - 18} ${y(line)} H ${W - RIGHT}`}
                  stroke={LINES[line].color}
                  strokeWidth={10}
                  strokeLinecap="round"
                  className="draw-line"
                  style={{ ["--len" as string]: `${len}`, ["--delay" as string]: `${i * 90}ms` }}
                />
              </g>
            );
          })}

          {stations.map((s, i) => {
            const active = i === selected;
            const interchange = s.lines.length > 1;
            const href = `/papers/${s.entry.paper.id}`;
            return (
              <a
                key={s.entry.paper.id}
                href={href}
                aria-label={`${s.entry.rank}. ${s.entry.paper.title}`}
                onMouseEnter={() => setSelected(i)}
                onFocus={() => setSelected(i)}
                className="group outline-none"
              >
                <g className="open-station" style={{ ["--delay" as string]: `${450 + i * 70}ms` }}>
                  <rect x={s.x - 26} y={s.y - 30} width={52} height={s.yTo - s.y + 60} fill="transparent" />
                  {active ? (
                    <rect
                      x={s.x - 16}
                      y={s.y - 16}
                      width={32}
                      height={s.yTo - s.y + 32}
                      rx={16}
                      fill="none"
                      stroke="var(--color-signal)"
                      strokeWidth={5}
                    />
                  ) : null}
                  {interchange ? (
                    // Transfer link: a cased connector that passes over the lines between, as on a metro map
                    <>
                      <path d={`M ${s.x} ${s.y} V ${s.yTo}`} stroke="#fff" strokeWidth={11} strokeLinecap="round" />
                      <path d={`M ${s.x} ${s.y} V ${s.yTo}`} stroke="var(--color-ink)" strokeWidth={3.5} />
                    </>
                  ) : null}
                  {s.ys.map((cy) => (
                    <circle key={cy} cx={s.x} cy={cy} r={8.5} fill="#fff" stroke="var(--color-ink)" strokeWidth={3.5} />
                  ))}
                  <text
                    x={s.x}
                    y={s.labelAbove ? s.y - 19 : s.yTo + 30}
                    textAnchor="middle"
                    paintOrder="stroke"
                    stroke="#fff"
                    strokeWidth={5}
                    strokeLinejoin="round"
                    className={`signage text-[15px] ${active ? "fill-ink font-bold" : "fill-ink-soft font-semibold"} group-focus-visible:underline`}
                  >
                    {s.name}
                  </text>
                </g>
              </a>
            );
          })}
        </svg>
        <figcaption className="mt-2 text-sm text-ink-soft">
          Most significant first, left to right. Linked stations are interchanges: papers that sit on two lines.
        </figcaption>
      </figure>

      {/* Station board for the focused station */}
      <aside aria-live="polite" className="hidden border-t-[6px] border-band bg-panel p-5 md:block">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <LineBullets lines={current.lines} size="md" />
          {current.entry.paper.change_type ? (
            <span className="text-sm font-bold">{CHANGE_TYPE_LABELS[current.entry.paper.change_type]}</span>
          ) : null}
          <span className="tabular ml-auto text-sm font-semibold text-ink-soft">
            {current.entry.rank} of {stations.length}
          </span>
        </div>
        <h3 className="mt-4 text-xl font-bold leading-snug">{current.entry.paper.title}</h3>
        <p className="mt-3 leading-relaxed">{current.entry.paper.what_changed}</p>
        <Link
          href={`/papers/${current.entry.paper.id}`}
          className="mt-4 inline-flex items-center gap-1 font-semibold text-link underline"
        >
          Read it at your level
        </Link>
      </aside>

      {/* Vertical strip map: phones */}
      <ol className="md:hidden" aria-label={`Stations in ${editionLabel}`}>
        {stations.map((s, i) => {
          const line = LINES[s.lines[0]];
          const last = i === stations.length - 1;
          return (
            <li key={s.entry.paper.id} className="grid grid-cols-[2.25rem_1fr] gap-3">
              <div className="relative flex justify-center" aria-hidden>
                <span className="absolute inset-y-0 w-2.5" style={{ background: line.color, bottom: last ? "50%" : 0 }} />
                <span
                  className={`relative mt-1.5 w-5 border-[3px] border-ink bg-white ${s.lines.length > 1 ? "h-8 rounded-[10px]" : "h-5 rounded-full"}`}
                />
              </div>
              <div className="pb-6">
                <LineBullets lines={s.lines} />
                <Link href={`/papers/${s.entry.paper.id}`} className="mt-1 block font-bold leading-snug text-ink no-underline">
                  {s.entry.paper.title}
                </Link>
                <p className="mt-1 line-clamp-3 text-[0.9375rem] leading-relaxed text-ink-soft">{s.entry.paper.what_changed}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
