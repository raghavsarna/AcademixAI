"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from "react";

import { api, getToken, setToken, subscribeToken } from "./client-api";
import type { User } from "./types";

type AuthState = {
  user: User | null;
  status: "loading" | "signed-in" | "signed-out";
  login: (login: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // The token lives in localStorage: an external store, unknown during server rendering.
  const token = useSyncExternalStore(subscribeToken, getToken, () => undefined);
  const [account, setAccount] = useState<{ token: string; user: User | null } | null>(null);

  useEffect(() => {
    if (!token || account?.token === token) return;
    let cancelled = false;
    api
      .me()
      .then((user) => !cancelled && setAccount({ token, user }))
      .catch(() => !cancelled && setAccount({ token, user: null }));
    return () => {
      cancelled = true;
    };
  }, [token, account?.token]);

  const user = token && account?.token === token ? account.user : null;
  const status: AuthState["status"] =
    token === undefined || (token && account?.token !== token) ? "loading" : user ? "signed-in" : "signed-out";

  const login = useCallback(async (login: string, password: string) => {
    const { access_token } = await api.login(login, password);
    setToken(access_token);
    const me = await api.me();
    setAccount({ token: access_token, user: me });
  }, []);

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      await api.register(email, username, password);
      await login(username, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    setToken(null);
    setAccount(null);
  }, []);

  const value = useMemo(() => ({ user, status, login, register, logout }), [user, status, login, register, logout]);
  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
