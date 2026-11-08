import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 py-20 sm:px-8">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
        No station here
      </h1>
      <p className="mt-4 max-w-[52ch] text-lg leading-relaxed text-ink-soft">
        That page doesn&rsquo;t exist, or the link is out of date.
      </p>
      <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 font-semibold">
        <Link href="/today" className="text-link underline">
          Today&rsquo;s edition
        </Link>
        <Link href="/editions" className="text-link underline">
          All editions
        </Link>
      </div>
    </div>
  );
}
