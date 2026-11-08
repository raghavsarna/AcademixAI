// Research lines: how arXiv categories map onto the metro map. Colours never change meaning.

export type LineId = "language" | "vision" | "learning" | "agents" | "robotics" | "other";

export type Line = {
  id: LineId;
  name: string;
  bullet: string;
  color: string;
  text: string; // text colour on the line colour
};

export const LINES: Record<LineId, Line> = {
  language: { id: "language", name: "Language", bullet: "L", color: "var(--color-line-language)", text: "#ffffff" },
  vision: { id: "vision", name: "Vision", bullet: "V", color: "var(--color-line-vision)", text: "#ffffff" },
  learning: { id: "learning", name: "Learning", bullet: "M", color: "var(--color-line-learning)", text: "#ffffff" },
  agents: { id: "agents", name: "Agents & reasoning", bullet: "A", color: "var(--color-line-agents)", text: "#141518" },
  robotics: { id: "robotics", name: "Robotics", bullet: "R", color: "var(--color-line-robotics)", text: "#ffffff" },
  other: { id: "other", name: "Other fields", bullet: "X", color: "var(--color-line-other)", text: "#ffffff" },
};

export const LINE_ORDER: LineId[] = ["language", "vision", "learning", "agents", "robotics", "other"];

const CATEGORY_TO_LINE: Record<string, LineId> = {
  "cs.CL": "language",
  "cs.CV": "vision",
  "eess.IV": "vision",
  "cs.LG": "learning",
  "stat.ML": "learning",
  "cs.NE": "learning",
  "cs.AI": "agents",
  "cs.MA": "agents",
  "cs.RO": "robotics",
};

export function lineForCategory(category: string): LineId {
  return CATEGORY_TO_LINE[category] ?? "other";
}

/** The paper's primary line, then any other lines it is cross-listed on (an interchange). */
export function linesForPaper(categories: string[]): LineId[] {
  const ids: LineId[] = [];
  for (const category of categories) {
    const id = lineForCategory(category);
    if (!ids.includes(id)) ids.push(id);
  }
  return ids.length ? ids : ["other"];
}

/** A short station name: the paper's own name before a colon, or its first words. */
export function stationName(title: string, max = 26): string {
  const named = title.split(/:\s/)[0].trim();
  if (named.length <= max && named.length < title.length) return named;
  if (title.length <= max) return title;
  const words = title.split(/\s+/);
  let name = "";
  for (const word of words) {
    if ((name + " " + word).trim().length > max - 1) break;
    name = (name + " " + word).trim();
  }
  return `${name}…`;
}
