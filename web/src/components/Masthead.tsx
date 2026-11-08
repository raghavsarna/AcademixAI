"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";

import { useAuth } from "@/lib/auth";

import { Wordmark } from "./Logo";

const NAV = [
  { href: "/today", label: "Today" },
  { href: "/editions", label: "All editions" },
  { href: "/explain", label: "Explain a paper" },
] as const;

/** The signage band: black, white type, the way a station announces where you are. */
function NavLinks({ pathname }: { pathname: string | null }) {
  return (
    <>
      {NAV.map((item) => {
        const active =
          pathname !== null && (pathname === item.href || (item.href === "/editions" && pathname.startsWith("/editions")));
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap rounded-sm px-2 py-1.5 text-[0.9375rem] font-semibold no-underline transition-colors duration-150 ${
              active ? "text-white underline decoration-signal decoration-[3px] underline-offset-[10px]" : "text-band-soft hover:text-white"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

/** Reads the URL, so it streams in after the static shell (Cache Components). */
function ActiveNavLinks() {
  return <NavLinks pathname={usePathname()} />;
}

export function Masthead() {
  const { user, status, logout } = useAuth();

  return (
    <header className="bg-band text-white">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:bg-signal focus:px-3 focus:py-2 focus:text-ink"
      >
        Skip to content
      </a>
      <div className="mx-auto flex max-w-[88rem] flex-wrap items-center gap-x-8 gap-y-3 px-5 py-4 sm:px-8">
        <Link href="/" className="rounded-sm text-white no-underline" aria-label="AcademixAI home">
          <Wordmark />
        </Link>
        <nav aria-label="Main" className="order-3 -mx-2 flex w-full gap-1 overflow-x-auto sm:order-none sm:mx-0 sm:w-auto">
          <Suspense fallback={<NavLinks pathname={null} />}>
            <ActiveNavLinks />
          </Suspense>
        </nav>
        <div className="ml-auto flex items-center gap-2 text-[0.9375rem] font-semibold">
          {status === "signed-in" && user ? (
            <>
              <Link href="/library" className="rounded-sm px-2 py-1.5 text-band-soft no-underline hover:text-white">
                {user.username}&rsquo;s papers
              </Link>
              <button
                type="button"
                onClick={logout}
                className="rounded-sm border border-white/30 px-3 py-1.5 text-white transition-colors duration-150 hover:border-white"
              >
                Log out
              </button>
            </>
          ) : status === "signed-out" ? (
            <>
              <Link href="/login" className="rounded-sm px-2 py-1.5 text-band-soft no-underline hover:text-white">
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-sm bg-white px-3 py-1.5 text-ink no-underline transition-colors duration-150 hover:bg-signal"
              >
                Sign up
              </Link>
            </>
          ) : (
            <span className="h-8 w-28" aria-hidden />
          )}
        </div>
      </div>
    </header>
  );
}
