import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

import type { User } from "../api/authApi";
import * as authApi from "../api/authApi";
import { apiClient } from "../api/http";
import type { paths } from "../api/generated/openapi";
import { clearAccessToken, getAccessToken, setAccessToken } from "../store/session";

type AuthContextValue = {
    user: User | null;
    loading: boolean;
    login: (input: { email: string; password: string; remember_me: boolean }) => Promise<void>;
    signup: (input: { email: string; name: string; password: string }) => Promise<void>;
    updateProfile: (input: { name?: string; profile_image_url?: string | null }) => Promise<void>;
    logout: () => Promise<void>;
    refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
type AppConfig = paths["/config"]["get"]["responses"][200]["content"]["application/json"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const refreshInFlightRef = useRef<Promise<void> | null>(null);

    const refreshSession = async () => {
        if (refreshInFlightRef.current) {
            return refreshInFlightRef.current;
        }

        const refreshTask = (async () => {
            const refreshResult = await authApi.refresh();
            setAccessToken(refreshResult.access_token);
            const me = await authApi.me();
            setUser(me);
        })();

        refreshInFlightRef.current = refreshTask;
        try {
            await refreshTask;
        } finally {
            refreshInFlightRef.current = null;
        }
    };

    useEffect(() => {
        // Agent customization note:
        // This bootstrap flow is the single place to plug SSO/session policies.
        const bootstrap = async () => {
            try {
                const { data: appConfig } = await apiClient.GET("/config");
                const config = appConfig as AppConfig | undefined;
                if (config?.login_enabled === false) {
                    if (config.bootstrap_access_token) {
                        setAccessToken(config.bootstrap_access_token);
                    } else {
                        clearAccessToken();
                    }
                    setUser(config.bootstrap_user ?? null);
                    return;
                }

                const token = getAccessToken();
                if (token) {
                    try {
                        const me = await authApi.me();
                        setUser(me);
                        return;
                    } catch {
                        clearAccessToken();
                    }
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
            updateProfile: async (input) => {
                const nextUser = await authApi.updateMe(input);
                setUser(nextUser);
            },
            logout: async () => {
                try {
                    await authApi.logout();
                } finally {
                    clearAccessToken();
                    setUser(null);
                }
            },
            refreshSession,
        }),
        [loading, user],
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
