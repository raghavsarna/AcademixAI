import type { Metadata } from "next";

import { AuthGate } from "@/components/AuthGate";
import { UploadForm } from "@/components/UploadForm";

export const metadata: Metadata = { title: "Explain a paper" };

export default function ExplainPage() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-10 sm:px-8 sm:pt-14">
      <h1 className="text-[2.25rem] font-extrabold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
        Explain a paper
      </h1>
      <p className="mt-4 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
        Upload a research paper as a PDF. You get what it changes, what it builds on, the explanation at Plain,
        Student and Expert depth, and a chat that answers at yours.
      </p>
      <AuthGate reason="Explaining a paper needs a free account, so your uploads stay yours." next="/explain">
        <UploadForm />
      </AuthGate>
    </div>
  );
}
