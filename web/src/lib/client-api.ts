"use client";

// Browser-side calls to the API (proxied to FastAPI by the /api rewrite).

import type { Depth, MyPaper, UploadJob, User } from "./types";

const TOKEN_KEY = "academixai.token";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

const TOKEN_EVENT = "academixai:token";

export function setToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage can be unavailable (private mode); the session then lasts for this page only.
  }
  window.dispatchEvent(new Event(TOKEN_EVENT));
}

/** Subscribe to token changes in this tab and in other tabs (for useSyncExternalStore). */
export function subscribeToken(callback: () => void): () => void {
  window.addEventListener(TOKEN_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(TOKEN_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function messageFrom(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) {
    const field = detail[0].loc?.at(-1);
    const message = String(detail[0].msg).replace(/^Value error, /, "");
    return field ? `${field[0].toUpperCase()}${field.slice(1)}: ${message}` : message;
  }
  if (status === 429) return "Too many requests. Please wait a minute and try again.";
  if (status >= 500) return "Something went wrong on our side. Please try again.";
  return "That didn't work. Please try again.";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) setToken(null);
    throw new ApiError(response.status, messageFrom(response.status, body));
  }
  return body as T;
}

export const api = {
  login: (login: string, password: string) =>
    request<{ access_token: string }>("/api/auth/token", {
      method: "POST",
      body: new URLSearchParams({ username: login, password }),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  register: (email: string, username: string, password: string) =>
    request<User>("/api/auth/register", { method: "POST", body: JSON.stringify({ email, username, password }) }),
  me: () => request<User>("/api/auth/me"),
  myPapers: () => request<MyPaper[]>("/api/papers"),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadJob>("/api/papers", { method: "POST", body: form });
  },
  uploadJobs: () => request<UploadJob[]>("/api/papers/jobs"),
  retryUpload: (id: string) => request<UploadJob>(`/api/papers/jobs/${encodeURIComponent(id)}/retry`, { method: "POST" }),
  dismissUpload: (id: string) => request<null>(`/api/papers/jobs/${encodeURIComponent(id)}`, { method: "DELETE" }),
  askPaper: (id: string, message: string, level: Depth) =>
    request<{ reply: string }>(`/api/papers/${encodeURIComponent(id)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, level }),
    }),
  askEdition: (date: string, message: string, level: Depth) =>
    request<{ reply: string }>(`/api/editions/${encodeURIComponent(date)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, level }),
    }),
};
