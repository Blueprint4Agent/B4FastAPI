import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
    type ReactNode,
} from "react";

import { useSystemApi } from "../api/system/useSystemApi";
import { isTauriRuntime } from "../../utils/desktopRuntime";

export type ServerConnectivityStatus = "checking" | "offline" | "online" | "reconnecting";

type ServerConnectivityContextValue = {
    isDesktop: boolean;
    status: ServerConnectivityStatus;
    lastConnectedAt: Date | null;
    retryCount: number;
    checkNow: () => Promise<void>;
};

const PROBE_TIMEOUT_MS = 3_000;
const ONLINE_PROBE_INTERVAL_MS = 30_000;
const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 30_000;

const BROWSER_CONNECTIVITY: ServerConnectivityContextValue = {
    isDesktop: false,
    status: "online",
    lastConnectedAt: null,
    retryCount: 0,
    checkNow: async () => undefined,
};

const ServerConnectivityContext =
    createContext<ServerConnectivityContextValue>(BROWSER_CONNECTIVITY);

export function getReconnectDelayMs(attempt: number, randomValue = Math.random()): number {
    const normalizedAttempt = Math.max(1, attempt);
    const exponentialDelay = Math.min(
        RECONNECT_BASE_DELAY_MS * 2 ** (normalizedAttempt - 1),
        RECONNECT_MAX_DELAY_MS,
    );
    const jitterMultiplier = 0.8 + Math.min(1, Math.max(0, randomValue)) * 0.4;
    return Math.round(exponentialDelay * jitterMultiplier);
}

export function ServerConnectivityProvider({ children }: { children: ReactNode }) {
    const { getServerReadiness, normalizeSystemError } = useSystemApi();
    const isDesktop = typeof window !== "undefined" && isTauriRuntime(window);
    const [status, setStatus] = useState<ServerConnectivityStatus>(
        isDesktop ? "checking" : "online",
    );
    const [lastConnectedAt, setLastConnectedAt] = useState<Date | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const checkNowRef = useRef<() => Promise<void>>(async () => undefined);

    useEffect(() => {
        if (!isDesktop) {
            checkNowRef.current = async () => undefined;
            return;
        }

        let active = true;
        let requestInFlight = false;
        let retryAttempt = 0;
        let lastKnownOnline = false;
        let timerId: number | null = null;
        let requestController: AbortController | null = null;

        const clearTimer = () => {
            if (timerId !== null) {
                window.clearTimeout(timerId);
                timerId = null;
            }
        };

        const scheduleProbe = (callback: () => void, delayMs: number) => {
            clearTimer();
            timerId = window.setTimeout(callback, delayMs);
        };

        const probe = async (reconnecting: boolean): Promise<void> => {
            if (!active || requestInFlight) {
                return;
            }

            if (!window.navigator.onLine) {
                lastKnownOnline = false;
                retryAttempt += 1;
                setStatus("offline");
                setRetryCount(retryAttempt);
                scheduleProbe(() => void probe(true), getReconnectDelayMs(retryAttempt));
                return;
            }

            clearTimer();
            requestInFlight = true;
            if (!lastKnownOnline) {
                setStatus(reconnecting ? "reconnecting" : "checking");
            }

            const controller = new AbortController();
            requestController = controller;
            const timeoutId = window.setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

            try {
                await getServerReadiness(controller.signal);
                if (!active) {
                    return;
                }
                lastKnownOnline = true;
                retryAttempt = 0;
                setRetryCount(0);
                setLastConnectedAt(new Date());
                setStatus("online");
                scheduleProbe(() => void probe(false), ONLINE_PROBE_INTERVAL_MS);
            } catch (error) {
                if (!active) {
                    return;
                }
                lastKnownOnline = false;
                retryAttempt += 1;
                setRetryCount(retryAttempt);
                setStatus("offline");
                const detail = normalizeSystemError(error);
                console.debug("[connectivity] server readiness check failed:", detail.message);
                scheduleProbe(() => void probe(true), getReconnectDelayMs(retryAttempt));
            } finally {
                window.clearTimeout(timeoutId);
                requestInFlight = false;
                if (requestController === controller) {
                    requestController = null;
                }
            }
        };

        const checkNow = async () => {
            await probe(!lastKnownOnline);
        };

        const handleOffline = () => {
            lastKnownOnline = false;
            requestController?.abort();
            setStatus("offline");
        };
        const handleOnline = () => {
            retryAttempt = 0;
            setRetryCount(0);
            void probe(true);
        };
        const handleFocus = () => {
            void probe(!lastKnownOnline);
        };
        const handleVisibilityChange = () => {
            if (document.visibilityState === "visible") {
                void probe(!lastKnownOnline);
            }
        };

        checkNowRef.current = checkNow;
        window.addEventListener("offline", handleOffline);
        window.addEventListener("online", handleOnline);
        window.addEventListener("focus", handleFocus);
        document.addEventListener("visibilitychange", handleVisibilityChange);
        void probe(false);

        return () => {
            active = false;
            clearTimer();
            requestController?.abort();
            checkNowRef.current = async () => undefined;
            window.removeEventListener("offline", handleOffline);
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("focus", handleFocus);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, [getServerReadiness, isDesktop, normalizeSystemError]);

    const checkNow = useCallback(async () => {
        await checkNowRef.current();
    }, []);

    const value = useMemo<ServerConnectivityContextValue>(
        () => ({ isDesktop, status, lastConnectedAt, retryCount, checkNow }),
        [checkNow, isDesktop, lastConnectedAt, retryCount, status],
    );

    return (
        <ServerConnectivityContext.Provider value={value}>
            {children}
        </ServerConnectivityContext.Provider>
    );
}

export function useServerConnectivity(): ServerConnectivityContextValue {
    return useContext(ServerConnectivityContext);
}
