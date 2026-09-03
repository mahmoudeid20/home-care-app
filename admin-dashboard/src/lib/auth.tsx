"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { ApiRequestError, login as apiLogin } from "./api";
import { clearTokens, getAccessToken, setTokens } from "./tokenStorage";
import type { AuthUser } from "./types";

interface JwtPayload {
  sub: string;
  role: string;
  exp: number;
}

function decodeJwt(token: string): JwtPayload | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Bootstrap from a stored token: /auth/login already returned the full
    // user object at sign-in time, but if the page was reloaded we only
    // have the JWT — decode role/sub from it. It's already been verified
    // signature-wise by the backend; we only read it here to decide what
    // to *render*, never to authorize anything (every real check happens
    // server-side).
    const token = getAccessToken();
    if (token) {
      const payload = decodeJwt(token);
      if (payload && payload.exp * 1000 > Date.now()) {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time session bootstrap from a stored token on mount, not a reactive sync loop
        setUser({
          id: payload.sub,
          role: payload.role as AuthUser["role"],
          email: "",
          phone: null,
          is_active: true,
          is_email_verified: true,
          is_phone_verified: true,
        });
      } else {
        clearTokens();
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const result = await apiLogin(email, password);
      if (result.user.role !== "ADMIN") {
        setError("This account is not an administrator.");
        return false;
      }
      setTokens(result.tokens.access_token, result.tokens.refresh_token);
      setUser(result.user);
      return true;
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError("Couldn't reach the server. Please try again.");
      }
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
