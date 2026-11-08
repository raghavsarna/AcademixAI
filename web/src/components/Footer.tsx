import Link from "next/link";

import { LINE_ORDER } from "@/lib/lines";

import { LineBullet } from "./LineBullet";
import { Wordmark } from "./Logo";

export function Footer() {
  return (
    <footer className="mt-24 bg-band text-white">
      <div className="mx-auto grid max-w-[88rem] gap-10 px-5 py-12 sm:px-8 lg:grid-cols-[1.2fr_2fr]">
        <div className="space-y-4">
          <Wordmark />
          <p className="max-w-sm text-sm leading-relaxed text-band-soft">
            What changed in AI research today, and every paper at your level. Papers come from arXiv; explanations
            are written by a language model, so check the paper before you cite it.
          </p>
        </div>
        <div className="grid gap-8 sm:grid-cols-2">
          <div>
            <h2 className="text-sm font-bold">Lines on the map</h2>
            <ul className="mt-3 grid gap-2">
              {LINE_ORDER.map((line) => (
                <li key={line}>
                  <LineBullet line={line} size="sm" label />
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="text-sm font-bold">Ride</h2>
            <ul className="mt-3 grid gap-2 text-sm text-band-soft">
              <li>
                <Link href="/today" className="no-underline hover:text-white">
                  Today&rsquo;s edition
                </Link>
              </li>
              <li>
                <Link href="/editions" className="no-underline hover:text-white">
                  All editions
                </Link>
              </li>
              <li>
                <Link href="/explain" className="no-underline hover:text-white">
                  Explain a paper
                </Link>
              </li>
              <li>
                <a href="https://github.com/raghavsarna/AcademixAI" className="no-underline hover:text-white">
                  Source on GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}
