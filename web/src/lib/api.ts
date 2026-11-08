// Server-side data access, fetched at request time so the site builds without a running API.
// Pages read these inside <Suspense> (or a route's loading.tsx) and stream in.
import "server-only";

import type { EditionDetail, EditionSummary, PaperDetail } from "./types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

async function getJSON<T>(path: string): Promise<T | null> {
  const response = await fetch(`${API_URL}${path}`, { headers: { Accept: "application/json" } });
  if (response.status === 404 || response.status === 422) return null;
  if (!response.ok) throw new Error(`API ${response.status} for ${path}`);
  return response.json() as Promise<T>;
}

export const getLatestEdition = () => getJSON<EditionDetail>("/api/editions/latest");

export const getEdition = (date: string) => getJSON<EditionDetail>(`/api/editions/${encodeURIComponent(date)}`);

export async function listEditions(limit = 60): Promise<EditionSummary[]> {
  return (await getJSON<EditionSummary[]>(`/api/editions?limit=${limit}`)) ?? [];
}

export const getPaper = (id: string) => getJSON<PaperDetail>(`/api/papers/${encodeURIComponent(id)}`);
