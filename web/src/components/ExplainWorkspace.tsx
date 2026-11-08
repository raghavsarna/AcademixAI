"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";

import { useAuth } from "@/lib/auth";
import type { UploadJob } from "@/lib/types";
import { useUploadJobs } from "@/lib/use-upload-jobs";

import { AuthGate } from "./AuthGate";
import { UploadForm } from "./UploadForm";
import { UploadJobs } from "./UploadJobs";
import { WhatYouGet } from "./WhatYouGet";

const RECENT_FINISHED = 3;

/**
 * The upload form beside the reader's uploads. A paper the reader starts here opens by itself
 * when it is ready, as long as they are still on this page; otherwise it waits in the list.
 */
export function ExplainWorkspace() {
  const router = useRouter();
  const { status } = useAuth();
  const signedIn = status === "signed-in";
  const { jobs, add, retry, dismiss } = useUploadJobs(signedIn);
  // The upload the reader just started here, to open when it is ready
  const following = useRef<string | null>(null);

  function started(job: UploadJob) {
    if (job.url) {
      router.push(job.url as never);
      return;
    }
    add(job);
    following.current = job.id;
  }

  async function retryAndFollow(id: string) {
    await retry(id);
    following.current = id;
  }

  // Open the paper the reader is waiting on as soon as it is ready
  useEffect(() => {
    const job = following.current ? jobs?.find((j) => j.id === following.current) : undefined;
    if (!job || (job.status !== "ready" && job.status !== "failed")) return;
    // Stop following first, so coming back to this page later doesn't open it again
    following.current = null;
    if (job.status === "ready" && job.url) router.push(job.url as never);
  }, [jobs, router]);

  // Uploads still being explained or that failed, then the few most recent finished ones;
  // older papers live in Your papers
  const unfinished = jobs?.filter((j) => j.status !== "ready") ?? [];
  const finished = jobs?.filter((j) => j.status === "ready") ?? [];
  const shown = [...unfinished, ...finished.slice(0, RECENT_FINISHED)];
  const showJobs = signedIn && shown.length > 0;
  return (
    <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-16">
      <div className="min-w-0">
        <AuthGate reason="Explaining a paper needs a free account, so your uploads stay yours." next="/explain">
          <UploadForm onStarted={started} />
        </AuthGate>
      </div>
      <div className="min-w-0">
        {showJobs ? (
          <section aria-labelledby="uploads-title">
            <h2 id="uploads-title" className="mb-4 text-xl font-bold">
              Your uploads
            </h2>
            <UploadJobs jobs={shown} onRetry={retryAndFollow} onDismiss={dismiss} />
            {finished.length > RECENT_FINISHED ? (
              <Link href="/library" className="mt-4 inline-block font-semibold text-link underline">
                All your papers
              </Link>
            ) : null}
          </section>
        ) : (
          <WhatYouGet />
        )}
      </div>
    </div>
  );
}
