import { DEPTH_LABELS, type Depth } from "@/lib/types";

/** Depth colours run from light to dark: the deeper the reading, the darker the sign. */
export const DEPTH_STYLE: Record<Depth, string> = {
  plain: "bg-depth-plain text-ink",
  student: "bg-depth-student text-ink",
  expert: "bg-depth-expert text-white",
};

export function DepthChip({ depth }: { depth: Depth }) {
  return (
    <span className={`signage inline-block rounded-[4px] px-2.5 py-1 text-sm font-bold ${DEPTH_STYLE[depth]}`}>
      {DEPTH_LABELS[depth]}
    </span>
  );
}
