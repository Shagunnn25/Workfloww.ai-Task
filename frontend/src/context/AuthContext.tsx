import { createContext, useContext, useState, type ReactNode } from "react";
import type { UserRole } from "../types/user";

export interface Session {
  token: string;
  role: UserRole;
  fullName: string;
}

interface AuthContextValue {
  session: Session | null;
  login: (session: Session) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// sessionStorage (not localStorage) so the token is cleared when the tab
// closes, limiting how long a stolen/leaked token stays usable. UI-side
// role branching below is a convenience only -- the backend and RLS are
// what actually enforce access, so a tampered client can't gain anything.
const STORAGE_KEY = "task_app_session";

function readStoredSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(readStoredSession);

  function login(newSession: Session) {
    setSession(newSession);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newSession));
    } catch {
      // sessionStorage unavailable (private browsing, etc.) -- the session
      // still works for this tab via React state, it just won't survive a reload.
    }
  }

  function logout() {
    setSession(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }

  return <AuthContext.Provider value={{ session, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
