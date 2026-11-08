// Server-side data access. Public data (editions, papers) is cached; it changes once a day.
import "server-only";

import { cacheLife, cacheTag } from "next/cache";

import type { EditionDetail, EditionSummary, PaperDetail } from "./types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export class NotFoundError extends Error {}

async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: { Accept: "application/json" } });
  if (response.status === 404) throw new NotFoundError(path);
  if (!response.ok) throw new Error(`API ${response.status} for ${path}`);
  return response.json() as Promise<T>;
}

export async function getLatestEdition(): Promise<EditionDetail | null> {
  "use cache";
  cacheLife("hours");
  cacheTag("editions");
  try {
    return await getJSON<EditionDetail>("/api/editions/latest");
  } catch (error) {
    if (error instanceof NotFoundError) return null;
    throw error;
  }
}

export async function getEdition(date: string): Promise<EditionDetail | null> {
  "use cache";
  cacheLife("hours");
  cacheTag("editions", `edition-${date}`);
  try {
    return await getJSON<EditionDetail>(`/api/editions/${encodeURIComponent(date)}`);
  } catch (error) {
    if (error instanceof NotFoundError) return null;
    throw error;
  }
}

export async function listEditions(limit = 60): Promise<EditionSummary[]> {
  "use cache";
  cacheLife("hours");
  cacheTag("editions");
  return getJSON<EditionSummary[]>(`/api/editions?limit=${limit}`);
}

export async function getPaper(id: string): Promise<PaperDetail | null> {
  "use cache";
  cacheLife("days");
  cacheTag(`paper-${id}`);
  try {
    return await getJSON<PaperDetail>(`/api/papers/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof NotFoundError) return null;
    throw error;
  }
}
