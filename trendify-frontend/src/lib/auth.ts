import { createContext, useContext } from "react";

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

export interface AuthCtx {
  user: User | null;
  loading: boolean;
  /** Re-read the signed-in user from the server. */
  reload: () => Promise<User | null>;
  setUser: (u: User | null) => void;
  login: (email: string, password: string, otp?: string) => Promise<User>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthCtx | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
