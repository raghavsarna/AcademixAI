// Lays an edition out as a metro diagram: lines run left to right, the day's papers are
// stations in rank order, and a paper on two lines is an interchange where the lines meet.
// Where possible one line bends at 45 degrees to run alongside the other through the
// station; when there is no room, the two stations are joined by an out-of-station link.

import { LINE_ORDER, type LineId, linesForPaper } from "./lines";

export const W = 1400;
const TERMINAL = 26; // line ends
const PAD_X = 104; // first and last station
export const TOP = 64;
const BOTTOM = 62;
export const GAP = 54;
const OFF = 18; // spacing between two lines running side by side
const JOG_PAD = 16; // straight run either side of a station on a bend
const STATION_HALF = 26; // horizontal room a station needs on its line

type Bend = { x1: number; x2: number; delta: number; yTo: number };

export type MetroStation<T> = {
  item: T;
  index: number;
  lines: LineId[];
  x: number;
  /** Station dot positions (one per line it serves). */
  dots: number[];
  kind: "single" | "joined" | "linked";
  label: string[];
  labelAbove: boolean;
  top: number;
  bottom: number;
};

export type MetroLayout<T> = {
  lines: LineId[];
  trackY: Record<string, number>;
  paths: Record<string, string>;
  stations: MetroStation<T>[];
  height: number;
};

function permutations<X>(items: X[]): X[][] {
  if (items.length <= 1) return [items];
  return items.flatMap((item, i) =>
    permutations([...items.slice(0, i), ...items.slice(i + 1)]).map((rest) => [item, ...rest]),
  );
}

/** Track order that keeps lines joined by interchanges next to each other. */
function orderLines(used: LineId[], pairs: [LineId, LineId][]): LineId[] {
  const base = LINE_ORDER.filter((l) => used.includes(l));
  if (!pairs.length || base.length > 6) return base;
  let best = base;
  let bestCost = Infinity;
  for (const order of permutations(base)) {
    const cost = pairs.reduce((sum, [a, b]) => sum + Math.abs(order.indexOf(a) - order.indexOf(b)) ** 2, 0);
    // Prefer the canonical order on ties so the map stays familiar from day to day
    const drift = order.reduce((sum, l, i) => sum + Math.abs(base.indexOf(l) - i), 0) / 100;
    if (cost + drift < bestCost) {
      best = order;
      bestCost = cost + drift;
    }
  }
  return best;
}

export function layoutMetro<T>(items: T[], categoriesOf: (item: T) => string[], nameOf: (item: T) => string): MetroLayout<T> {
  const servedBy = items.map((item) => linesForPaper(categoriesOf(item)).slice(0, 2));
  const used = [...new Set(servedBy.flat())];
  const pairs = servedBy.filter((l) => l.length === 2) as [LineId, LineId][];
  const lines = orderLines(used, pairs);
  const trackY: Record<string, number> = Object.fromEntries(lines.map((l, i) => [l, TOP + i * GAP]));

  const step = items.length > 1 ? (W - 2 * PAD_X) / (items.length - 1) : 0;
  const xs = items.map((_, i) => (items.length > 1 ? PAD_X + i * step : W / 2));

  // What each line already has to carry: its own stations and any bends
  const busy: Record<string, [number, number][]> = Object.fromEntries(lines.map((l) => [l, []]));
  servedBy.forEach((own, i) => busy[own[0]].push([xs[i] - STATION_HALF, xs[i] + STATION_HALF]));
  const bends: Record<string, Bend[]> = Object.fromEntries(lines.map((l) => [l, []]));

  const free = (line: LineId, from: number, to: number, ignore?: [number, number]) =>
    from > TERMINAL + 12 &&
    to < W - TERMINAL - 12 &&
    busy[line].every(([a, b]) => (ignore && a === ignore[0] && b === ignore[1]) || b < from || a > to);

  const stations: MetroStation<T>[] = items.map((item, i) => {
    const own = servedBy[i];
    const x = xs[i];
    const name = [nameOf(item)];
    if (own.length === 1) {
      const y = trackY[own[0]];
      return { item, index: i, lines: own, x, dots: [y], kind: "single", label: name, labelAbove: true, top: y, bottom: y };
    }

    const [a, b] = own;
    const ya = trackY[a];
    const yb = trackY[b];
    // Try bending the secondary line alongside the primary, then the other way round
    const here: [number, number] = [x - STATION_HALF, x + STATION_HALF];
    const attempts: { mover: LineId; anchorLine: LineId; anchor: number; target: number; ignore?: [number, number] }[] = [
      { mover: b, anchorLine: a, anchor: ya, target: yb },
      { mover: a, anchorLine: b, anchor: yb, target: ya, ignore: here },
    ];
    for (const { mover, anchorLine, anchor, target, ignore } of attempts) {
      const yTo = anchor + Math.sign(target - anchor) * OFF;
      const delta = Math.abs(target - yTo);
      const x1 = x - JOG_PAD - delta;
      const x2 = x + JOG_PAD + delta;
      // The station also sits on the anchor line, which must be clear there (its own station excepted)
      const anchorClear = anchorLine === a || free(anchorLine, here[0], here[1]);
      if (anchorClear && free(mover, x1, x2, ignore)) {
        busy[mover].push([x1, x2]);
        if (anchorLine !== a) busy[anchorLine].push(here);
        bends[mover].push({ x1, x2, delta, yTo });
        const dots = [anchor, yTo].sort((p, q) => p - q);
        return {
          item,
          index: i,
          lines: own,
          x,
          dots,
          kind: "joined",
          label: name,
          labelAbove: true,
          top: dots[0],
          bottom: dots[1],
        };
      }
    }
    busy[b].push(here);
    const dots = [ya, yb].sort((p, q) => p - q);
    return { item, index: i, lines: own, x, dots, kind: "linked", label: name, labelAbove: true, top: dots[0], bottom: dots[1] };
  });

  // Place each label above or below its station, whichever collides least with the lines,
  // the bends, the other stations and the labels already placed (in rank order).
  type Box = [number, number, number, number]; // x1, y1, x2, y2
  const overlap = (a: Box, b: Box) =>
    Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const obstacles: Box[] = [];
  for (const line of lines) {
    const y = trackY[line];
    obstacles.push([TERMINAL, y - 8, W - TERMINAL, y + 8]);
    for (const bend of bends[line]) {
      obstacles.push([bend.x1, Math.min(y, bend.yTo) - 8, bend.x2, Math.max(y, bend.yTo) + 8]);
    }
  }
  for (const s of stations) obstacles.push([s.x - 16, s.top - 16, s.x + 16, s.bottom + 16]);
  const placed: Box[] = [];
  for (const s of stations) {
    const width = s.label[0].length * 8.2 + 8;
    const above: Box = [s.x - width / 2, s.top - 38, s.x + width / 2, s.top - 19];
    const below: Box = [s.x - width / 2, s.bottom + 19, s.x + width / 2, s.bottom + 38];
    const cost = (box: Box) =>
      obstacles.reduce((sum, o) => sum + overlap(box, o), 0) + placed.reduce((sum, o) => sum + 3 * overlap(box, o), 0);
    s.labelAbove = cost(above) <= cost(below);
    placed.push(s.labelAbove ? above : below);
  }

  const paths: Record<string, string> = {};
  for (const line of lines) {
    const y = trackY[line];
    let d = `M ${TERMINAL} ${y}`;
    for (const bend of [...bends[line]].sort((p, q) => p.x1 - q.x1)) {
      d += ` H ${bend.x1} L ${bend.x1 + bend.delta} ${bend.yTo} H ${bend.x2 - bend.delta} L ${bend.x2} ${y}`;
    }
    paths[line] = `${d} H ${W - TERMINAL}`;
  }

  const bottomY = TOP + (lines.length - 1) * GAP;
  return { lines, trackY, paths, stations, height: bottomY + BOTTOM };
}
