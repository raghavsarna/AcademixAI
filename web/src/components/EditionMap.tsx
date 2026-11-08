"use client";

import Link from "next/link";
import { type ReactNode, useMemo, useState } from "react";

import { LINES, type LineId } from "@/lib/lines";
import { layoutMetro, type MetroLayout, type MetroStation, W } from "@/lib/metro-layout";
import { CHANGE_TYPE_LABELS, type PaperCard } from "@/lib/types";

import { LineBullet, LineBullets } from "./LineBullet";

type Entry = { rank: number; paper: PaperCard };
type Station = MetroStation<Entry>;

/** The day's papers as a metro map, with a station board for the open station. */
export function EditionMap({
  entries,
  editionLabel,
  variant,
  intro,
  band,
}: {
  entries: Entry[];
  editionLabel: string;
  variant: "hero" | "page";
  intro?: ReactNode;
  band?: ReactNode;
}) {
  const map = useMemo(
    () =>
      layoutMetro(
        entries,
        (e) => e.paper.categories,
        (e) => e.paper.title,
      ),
    [entries],
  );
  const [selected, setSelected] = useState(0);
  const current = map.stations[selected] ?? map.stations[0];
  if (!current) return null;

  const board = <StationBoard station={current} total={map.stations.length} />;
  const diagram = <Diagram map={map} selected={selected} onSelect={setSelected} label={editionLabel} />;

  if (variant === "hero") {
    return (
      <div>
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(20rem,1fr)] lg:items-end">
          <div>{intro}</div>
          <div className="hidden md:block">{board}</div>
        </div>
        {band ? <div className="mt-6">{band}</div> : null}
        <div className="mt-3 hidden md:block">{diagram}</div>
        <Legend lines={map.lines} />
        <StripMap stations={map.stations} label={editionLabel} />
      </div>
    );
  }

  const pct = (current.x / W) * 100;
  return (
    <div>
      {band}
      <div className="mt-5 hidden md:block">{diagram}</div>
      <Legend lines={map.lines} />
      {/* The board hangs under the open station */}
      <div className="relative mt-5 hidden md:block">
        <div
          className="relative w-[26rem] max-w-full transition-[left] duration-250 ease-[cubic-bezier(0.22,1,0.36,1)]"
          style={{ left: `clamp(0px, calc(${pct}% - 13rem), calc(100% - 26rem))` }}
        >
          {board}
        </div>
      </div>
      <StripMap stations={map.stations} label={editionLabel} />
    </div>
  );
}

function Diagram({
  map,
  selected,
  onSelect,
  label,
}: {
  map: MetroLayout<Entry>;
  selected: number;
  onSelect: (i: number) => void;
  label: string;
}) {
  return (
    <figure>
      <svg
        viewBox={`0 0 ${W} ${map.height}`}
        className="w-full overflow-visible"
        role="group"
        aria-label={`Metro map of ${label}: ${map.stations.length} papers on ${map.lines.length} research lines`}
      >
        {map.lines.map((line, i) => (
          <path
            key={line}
            d={map.paths[line]}
            fill="none"
            stroke={LINES[line].color}
            strokeWidth={13}
            strokeLinecap="round"
            strokeLinejoin="round"
            pathLength={1}
            className="draw-line"
            style={{ ["--len" as string]: "1", ["--delay" as string]: `${i * 90}ms` }}
          />
        ))}

        {map.lines.map((line) => (
          <g key={line} aria-hidden>
            <circle cx={26} cy={map.trackY[line]} r={17} fill={LINES[line].color} />
            <text x={26} y={map.trackY[line] + 6} textAnchor="middle" className="text-[17px] font-bold" fill={LINES[line].text}>
              {LINES[line].bullet}
            </text>
          </g>
        ))}

        {map.stations.map((s, i) => (
          <StationMark key={s.item.paper.id} station={s} active={i === selected} onSelect={() => onSelect(i)} />
        ))}
      </svg>
    </figure>
  );
}

function StationMark({ station: s, active, onSelect }: { station: Station; active: boolean; onSelect: () => void }) {
  const span = s.bottom - s.top;
  const labelY = s.labelAbove ? s.top - 24 : s.bottom + 34;
  return (
    <a
      href={`/papers/${s.item.paper.id}`}
      aria-label={`${s.item.rank}. ${s.item.paper.title}`}
      onMouseEnter={onSelect}
      onFocus={onSelect}
      className="group outline-none"
    >
      <g className="open-station" style={{ ["--delay" as string]: `${500 + s.index * 70}ms` }}>
        <rect x={s.x - 30} y={s.top - 34} width={60} height={span + 68} fill="transparent" />
        {active ? (
          <rect
            x={s.x - 19}
            y={s.top - 19}
            width={38}
            height={span + 38}
            rx={19}
            fill="none"
            stroke="var(--color-signal)"
            strokeWidth={6}
          />
        ) : null}
        {s.kind === "joined" ? (
          // Interchange: a white capsule across the two lines running side by side
          <rect
            x={s.x - 12}
            y={s.top - 12}
            width={24}
            height={span + 24}
            rx={12}
            fill="#fff"
            stroke="var(--color-ink)"
            strokeWidth={4}
          />
        ) : s.kind === "linked" ? (
          // Out-of-station interchange: two stations joined by a thin link
          <>
            <path d={`M ${s.x} ${s.top} V ${s.bottom}`} stroke="var(--color-ink)" strokeWidth={3} />
            {s.dots.map((y) => (
              <circle key={y} cx={s.x} cy={y} r={10} fill="#fff" stroke="var(--color-ink)" strokeWidth={4} />
            ))}
          </>
        ) : (
          <circle cx={s.x} cy={s.top} r={10} fill="#fff" stroke="var(--color-ink)" strokeWidth={4} />
        )}
        <text
          x={s.x}
          y={labelY}
          textAnchor="middle"
          paintOrder="stroke"
          stroke="#fff"
          strokeWidth={6}
          strokeLinejoin="round"
          className={`signage text-[16px] font-bold ${active ? "fill-ink" : "fill-[#2b2d31]"} group-focus-visible:underline`}
        >
          {s.label.map((line, i) => (
            <tspan key={i} x={s.x} dy={i === 0 ? 0 : 17}>
              {line}
            </tspan>
          ))}
        </text>
      </g>
    </a>
  );
}

function StationBoard({ station, total }: { station: Station; total: number }) {
  const paper = station.item.paper;
  const meta = [
    paper.change_type ? CHANGE_TYPE_LABELS[paper.change_type] : null,
    station.lines.map((l) => LINES[l].name).join(" + "),
  ].filter(Boolean);
  return (
    <aside aria-live="polite" className="border-t-[6px] border-band bg-panel p-5">
      <div className="flex items-center justify-between gap-3">
        <LineBullets lines={station.lines} size="md" />
        <span className="tabular text-sm font-semibold text-ink-soft">
          Station {station.item.rank} of {total}
        </span>
      </div>
      <h2 className="mt-4 text-xl font-bold leading-snug">{paper.title}</h2>
      <p className="mt-1 text-sm font-semibold text-ink-soft">{meta.join(" · ")}</p>
      <p className="mt-3 line-clamp-4 leading-relaxed">{paper.what_changed}</p>
      <Link href={`/papers/${paper.id}`} className="mt-4 inline-block font-semibold text-link underline">
        Read it at your level
      </Link>
    </aside>
  );
}

function Legend({ lines }: { lines: LineId[] }) {
  return (
    <div className="mt-4 hidden flex-wrap items-center gap-x-6 gap-y-2 md:flex">
      <ul className="flex flex-wrap gap-x-5 gap-y-2" aria-label="Lines on this map">
        {lines.map((line) => (
          <li key={line}>
            <LineBullet line={line} size="sm" label />
          </li>
        ))}
      </ul>
      <p className="text-sm text-ink-soft">
        Most significant first, left to right. A white capsule is an interchange: a paper on two lines.
      </p>
    </div>
  );
}

/** Phones: a vertical strip map, one station per paper. */
function StripMap({ stations, label }: { stations: Station[]; label: string }) {
  return (
    <ol className="mt-6 md:hidden" aria-label={`Stations in ${label}`}>
      {stations.map((s, i) => {
        const line = LINES[s.lines[0]];
        const last = i === stations.length - 1;
        return (
          <li key={s.item.paper.id} className="grid grid-cols-[2.25rem_1fr] gap-3">
            <div className="relative flex justify-center" aria-hidden>
              <span className="absolute inset-y-0 w-2.5" style={{ background: line.color, bottom: last ? "50%" : 0 }} />
              <span
                className={`relative mt-1.5 w-5 border-[3px] border-ink bg-white ${s.lines.length > 1 ? "h-8 rounded-[10px]" : "h-5 rounded-full"}`}
              />
            </div>
            <div className="pb-6">
              <LineBullets lines={s.lines} />
              <Link href={`/papers/${s.item.paper.id}`} className="mt-1 block font-bold leading-snug text-ink no-underline">
                {s.item.paper.title}
              </Link>
              <p className="mt-1 line-clamp-3 text-[0.9375rem] leading-relaxed text-ink-soft">{s.item.paper.what_changed}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
