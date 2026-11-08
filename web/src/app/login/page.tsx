import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Log in" };

export default function Page() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-10 sm:px-8 sm:pt-14">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">Log in</h1>
      <p className="mt-4 max-w-[52ch] text-lg leading-relaxed text-ink-soft">Welcome back. Pick up where you left off.</p>
      <Suspense fallback={<div className="mt-8 h-72 max-w-md bg-panel" />}>
        <AuthForm mode="login" />
      </Suspense>
    </div>
  );
}
