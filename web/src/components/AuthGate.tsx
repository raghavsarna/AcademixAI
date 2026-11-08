"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";

/** Shows children to signed-in readers, and a clear way in to everyone else. */
export function AuthGate({ children, reason, next }: { children: React.ReactNode; reason: string; next: string }) {
  const { status } = useAuth();
  if (status === "loading") {
    return <div className="h-56 max-w-2xl rounded-[3px] bg-panel motion-safe:animate-pulse" aria-busy="true" />;
  }
  if (status === "signed-out") {
    return (
      <div className="max-w-2xl border border-rule p-6">
        <p className="text-lg leading-relaxed">{reason}</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href={`/signup?next=${encodeURIComponent(next)}` as never}
            className="rounded-[4px] bg-band px-5 py-2.5 font-semibold text-white no-underline hover:bg-ink"
          >
            Create a free account
          </Link>
          <Link
            href={`/login?next=${encodeURIComponent(next)}` as never}
            className="rounded-[4px] border border-rule-strong px-5 py-2.5 font-semibold text-ink no-underline hover:border-ink"
          >
            Log in
          </Link>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}
