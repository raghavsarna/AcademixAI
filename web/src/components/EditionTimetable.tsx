import Link from "next/link";

import { formatEditionDate, numberFormat } from "@/lib/format";
import type { EditionSummary } from "@/lib/types";

/** Editions set as a timetable: date, the day's biggest change, and the counts. */
export function EditionTimetable({ editions, caption }: { editions: EditionSummary[]; caption: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[40rem] border-collapse text-left">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="bg-band text-sm text-white">
            <th scope="col" className="px-4 py-3 font-bold">
              Date
            </th>
            <th scope="col" className="px-4 py-3 font-bold">
              Biggest change
            </th>
            <th scope="col" className="px-4 py-3 text-right font-bold">
              Changes
            </th>
            <th scope="col" className="px-4 py-3 text-right font-bold">
              Papers scanned
            </th>
          </tr>
        </thead>
        <tbody>
          {editions.map((e) => (
            <tr key={e.id} className="border-b border-rule align-top transition-colors duration-150 hover:bg-panel">
              <td className="whitespace-nowrap px-4 py-4">
                <time dateTime={e.edition_date} className="font-semibold">
                  {formatEditionDate(e.edition_date)}
                </time>
              </td>
              <td className="px-4 py-4">
                <Link href={`/editions/${e.edition_date}`} className="font-bold text-ink no-underline hover:underline">
                  {e.headline}
                </Link>
              </td>
              <td className="tabular px-4 py-4 text-right">{e.entry_count}</td>
              <td className="tabular px-4 py-4 text-right text-ink-soft">{numberFormat.format(e.papers_scanned)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
