"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, getToken, setToken } from "./client-api";
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
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthState["status"]>("loading");

  useEffect(() => {
    if (!getToken()) {
      setStatus("signed-out");
      return;
    }
    api
      .me()
      .then((me) => {
        setUser(me);
        setStatus("signed-in");
      })
      .catch(() => setStatus("signed-out"));
  }, []);

  const login = useCallback(async (login: string, password: string) => {
    const { access_token } = await api.login(login, password);
    setToken(access_token);
    const me = await api.me();
    setUser(me);
    setStatus("signed-in");
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
    setUser(null);
    setStatus("signed-out");
  }, []);

  const value = useMemo(() => ({ user, status, login, register, logout }), [user, status, login, register, logout]);
  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
