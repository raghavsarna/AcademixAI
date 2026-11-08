/** "Wednesday 5 November 2026" for an ISO date, without timezone drift. */
export function formatEditionDate(iso: string, style: "long" | "short" = "long"): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return new Intl.DateTimeFormat("en-GB", {
    weekday: style === "long" ? "long" : undefined,
    day: "numeric",
    month: style === "long" ? "long" : "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

/** "8 Nov 2026" for an ISO timestamp, in the reader's own timezone. */
export function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export const numberFormat = new Intl.NumberFormat("en-GB");
