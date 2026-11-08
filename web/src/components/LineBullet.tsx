import { LINES, type LineId } from "@/lib/lines";

type Props = { line: LineId; size?: "sm" | "md" | "lg"; label?: boolean };

const SIZES = { sm: "size-5 text-[11px]", md: "size-7 text-sm", lg: "size-10 text-xl" };

/** A round route bullet: the line's colour and letter, the way metro signage marks a service. */
export function LineBullet({ line, size = "md", label = false }: Props) {
  const l = LINES[line];
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`${SIZES[size]} inline-grid shrink-0 place-items-center rounded-full font-bold leading-none`}
        style={{ background: l.color, color: l.text }}
        aria-hidden={label ? true : undefined}
        title={label ? undefined : `${l.name} line`}
      >
        {l.bullet}
      </span>
      {label ? <span className="signage text-sm font-semibold">{l.name}</span> : null}
    </span>
  );
}

export function LineBullets({ lines, size = "sm" }: { lines: LineId[]; size?: Props["size"] }) {
  return (
    <span className="inline-flex items-center gap-1" aria-label={`${lines.map((l) => LINES[l].name).join(", ")} line`}>
      {lines.map((line) => (
        <span key={line} aria-hidden>
          <LineBullet line={line} size={size} />
        </span>
      ))}
    </span>
  );
}
