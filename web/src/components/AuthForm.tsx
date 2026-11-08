"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/client-api";

function safeNext(value: string | null): string {
  // Only same-site paths, so a crafted link can't send someone elsewhere after login.
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/today";
}

const field =
  "mt-1.5 w-full rounded-[4px] border border-rule-strong bg-ground px-3.5 py-2.5 text-base placeholder:text-ink-soft focus-visible:border-link aria-[invalid=true]:border-danger";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get("next"));
  const { login, register } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(String(form.get("login")), String(form.get("password")));
      } else {
        await register(String(form.get("email")), String(form.get("username")), String(form.get("password")));
      }
      router.push(next as never);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reach AcademixAI. Check your connection and try again.");
      setBusy(false);
    }
  }

  const other = mode === "login" ? "/signup" : "/login";
  return (
    <form onSubmit={submit} className="mt-8 grid max-w-md gap-5" noValidate={false}>
      {mode === "signup" ? (
        <>
          <div>
            <label htmlFor="email" className="font-semibold">
              Email
            </label>
            <input id="email" name="email" type="email" autoComplete="email" required className={field} aria-invalid={!!error} />
          </div>
          <div>
            <label htmlFor="username" className="font-semibold">
              Username
            </label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              required
              minLength={3}
              maxLength={50}
              pattern="[A-Za-z0-9_.\-]+"
              aria-describedby="username-hint"
              className={field}
              aria-invalid={!!error}
            />
            <p id="username-hint" className="mt-1 text-sm text-ink-soft">
              3 to 50 letters, numbers, dots, dashes or underscores.
            </p>
          </div>
        </>
      ) : (
        <div>
          <label htmlFor="login" className="font-semibold">
            Username or email
          </label>
          <input id="login" name="login" autoComplete="username" required className={field} aria-invalid={!!error} />
        </div>
      )}
      <div>
        <label htmlFor="password" className="font-semibold">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          required
          minLength={mode === "signup" ? 8 : undefined}
          aria-describedby={mode === "signup" ? "password-hint" : undefined}
          className={field}
          aria-invalid={!!error}
        />
        {mode === "signup" ? (
          <p id="password-hint" className="mt-1 text-sm text-ink-soft">
            At least 8 characters.
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="font-semibold text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={busy}
        className="rounded-[4px] bg-band px-6 py-3 text-lg font-bold text-white transition-colors duration-150 hover:bg-ink disabled:cursor-wait disabled:opacity-60"
      >
        {busy ? (mode === "login" ? "Logging in…" : "Creating your account…") : mode === "login" ? "Log in" : "Create account"}
      </button>
      <p className="text-ink-soft">
        {mode === "login" ? "New here? " : "Already have an account? "}
        <Link href={`${other}?next=${encodeURIComponent(next)}` as never} className="font-semibold text-link underline">
          {mode === "login" ? "Create an account" : "Log in"}
        </Link>
      </p>
    </form>
  );
}
