import type { Metadata } from "next";

import { AuthGate } from "@/components/AuthGate";
import { MyPapers } from "@/components/MyPapers";

export const metadata: Metadata = { title: "Your papers" };

export default function LibraryPage() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-10 sm:px-8 sm:pt-14">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">Your papers</h1>
      <p className="mt-4 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
        Every paper you have explained. Only you see this list; a paper&rsquo;s page can be shared by its link.
      </p>
      <div className="mt-8">
        <AuthGate reason="Log in to see the papers you have explained." next="/library">
          <MyPapers />
        </AuthGate>
      </div>
    </div>
  );
}
