import { createContext, useContext, useEffect, useMemo, useState } from "react";

import * as authApi from "../api/authApi";
import type { User } from "../api/types";
import { clearAccessToken, getAccessToken, setAccessToken } from "../store/session";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (input: { email: string; password: string; remember_me: boolean }) => Promise<void>;
  signup: (input: { email: string; name: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = async () => {
    const refreshResult = await authApi.refresh();
    setAccessToken(refreshResult.access_token);
    const me = await authApi.me();
    setUser(me);
  };

  useEffect(() => {
    // Agent customization note:
    // This bootstrap flow is the single place to plug SSO/session policies.
    const bootstrap = async () => {
      try {
        const token = getAccessToken();
        if (token) {
          const me = await authApi.me();
          setUser(me);
          return;
        }

        await refreshSession();
      } catch {
        clearAccessToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    void bootstrap();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (input) => {
        const payload = await authApi.login(input);
        setAccessToken(payload.access_token);
        setUser(payload.user);
      },
      signup: async (input) => {
        await authApi.signup(input);
      },
      logout: async () => {
        try {
          await authApi.logout();
        } finally {
          clearAccessToken();
          setUser(null);
        }
      },
      refreshSession
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used inside <AuthProvider>.");
  }
  return context;
}
