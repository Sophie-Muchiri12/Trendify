import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, hasRefreshCookie, refreshSession } from "@/lib/api";

export interface User {
  user_id: number;
  name: string;
  email: string;
  phone_number: string;
  role: "customer" | "admin";
  email_verified: boolean;
  mfa_enabled: boolean;
  created_at: string | null;
}

interface AuthCtx {
  user: User | null;
  loading: boolean;
  /** Re-read the signed-in user from the server. */
  reload: () => Promise<User | null>;
  setUser: (u: User | null) => void;
  login: (email: string, password: string, otp?: string) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthCtx | null>(null);

async function fetchMe(): Promise<User | null> {
  let { user } = await api<{ user: User | null }>("/auth/me");
  // The short-lived access cookie may have expired while the refresh cookie is still valid.
  if (!user && hasRefreshCookie() && (await refreshSession())) {
    ({ user } = await api<{ user: User | null }>("/auth/me"));
  }
  return user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    try {
      const u = await fetchMe();
      setUser(u);
      return u;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const login = useCallback(async (email: string, password: string, otp?: string) => {
    const { user: u } = await api<{ user: User }>("/auth/login", {
      method: "POST",
      body: otp ? { email, password, otp } : { email, password },
    });
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, reload, setUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
