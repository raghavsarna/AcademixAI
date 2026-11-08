"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mx-auto max-w-[88rem] px-5 py-20 sm:px-8">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
        Service is interrupted
      </h1>
      <p className="mt-4 max-w-[52ch] text-lg leading-relaxed text-ink-soft">
        We couldn&rsquo;t load this page. The research service may be restarting; try again in a moment.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-[4px] bg-band px-5 py-2.5 font-semibold text-white transition-colors duration-150 hover:bg-ink"
      >
        Try again
      </button>
    </div>
  );
}
