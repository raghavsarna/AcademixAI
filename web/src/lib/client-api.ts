"use client";

// Browser-side calls to the API (proxied to FastAPI by the /api rewrite).

import type { ChatAnswer, ChatSource, Depth, MyPaper, UploadJob, User } from "./types";

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

/** What a streamed answer reports as it arrives. */
export type StreamHandlers = {
  onStatus?: (detail: string) => void;
  onSources?: (sources: ChatSource[]) => void;
  onText: (text: string) => void;
};

/**
 * Ask about a paper and receive the answer as it is written (server-sent events). Resolves when the
 * answer is complete; rejects with an ApiError if the request is refused or the answer fails part-way.
 */
async function streamPaperAnswer(id: string, message: string, level: Depth, handlers: StreamHandlers): Promise<void> {
  const headers = new Headers({ "Content-Type": "application/json", Accept: "text/event-stream" });
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`/api/papers/${encodeURIComponent(id)}/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, level }),
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    if (response.status === 401 && token) setToken(null);
    throw new ApiError(response.status, messageFrom(response.status, body));
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let finished = false;
  while (!finished) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
      const name = /^event: (.*)$/m.exec(block)?.[1];
      const data = JSON.parse(/^data: (.*)$/m.exec(block)?.[1] ?? "null");
      if (name === "status") handlers.onStatus?.(data.detail);
      else if (name === "sources") handlers.onSources?.(data);
      else if (name === "delta") handlers.onText(data.text);
      else if (name === "error") throw new ApiError(502, data.detail);
      else if (name === "done") finished = true;
    }
  }
  if (!finished) throw new ApiError(502, "The answer was cut off. Try asking again.");
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
  deletePaper: (id: string) => request<null>(`/api/papers/${encodeURIComponent(id)}`, { method: "DELETE" }),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadJob>("/api/papers", { method: "POST", body: form });
  },
  uploadJobs: () => request<UploadJob[]>("/api/papers/jobs"),
  retryUpload: (id: string) => request<UploadJob>(`/api/papers/jobs/${encodeURIComponent(id)}/retry`, { method: "POST" }),
  dismissUpload: (id: string) => request<null>(`/api/papers/jobs/${encodeURIComponent(id)}`, { method: "DELETE" }),
  streamPaperAnswer,
  askPaper: (id: string, message: string, level: Depth) =>
    request<ChatAnswer>(`/api/papers/${encodeURIComponent(id)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, level }),
    }),
  askEdition: (date: string, message: string, level: Depth) =>
    request<ChatAnswer>(`/api/editions/${encodeURIComponent(date)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, level }),
    }),
};
