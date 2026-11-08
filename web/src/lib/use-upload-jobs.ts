"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./client-api";
import { ACTIVE_JOB, type UploadJob } from "./types";

const POLL_MS = 2000;

/**
 * The reader's recent uploads, kept in step with the server. While any upload is still being
 * explained the list is polled; it also refreshes when the tab becomes visible again. The server
 * is the only source of truth, so leaving the page, going back or reloading never shows a stale
 * state.
 */
export function useUploadJobs(enabled: boolean) {
  const [jobs, setJobs] = useState<UploadJob[] | null>(null);
  const [error, setError] = useState(false);
  const alive = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const next = await api.uploadJobs();
      if (alive.current) {
        setJobs(next);
        setError(false);
      }
    } catch {
      if (alive.current) setError(true);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    if (!enabled) return;
    // Fetching on mount is the point of this effect: the list lives on the server
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const onVisible = () => document.visibilityState === "visible" && refresh();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      alive.current = false;
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [enabled, refresh]);

  const active = jobs?.some((j) => ACTIVE_JOB.includes(j.status)) ?? false;
  useEffect(() => {
    if (!enabled || !active) return;
    const timer = window.setInterval(refresh, POLL_MS);
    return () => window.clearInterval(timer);
  }, [enabled, active, refresh]);

  /** Show a job the reader just started before the next poll picks it up. */
  const add = useCallback((job: UploadJob) => {
    setJobs((current) => [job, ...(current ?? []).filter((j) => j.id !== job.id)]);
  }, []);

  const retry = useCallback(
    async (id: string) => {
      const job = await api.retryUpload(id);
      add(job);
    },
    [add],
  );

  const dismiss = useCallback(async (id: string) => {
    await api.dismissUpload(id);
    setJobs((current) => (current ?? []).filter((j) => j.id !== id));
  }, []);

  return { jobs, error, refresh, add, retry, dismiss };
}
