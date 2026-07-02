import { useEffect, useRef } from "react";

import { useEventsApi, type RealtimeEvent } from "../../api/events/useEventsApi";
import { useServerConnectivity } from "../../connectivity/useServerConnectivity";

type UseRealtimeStreamSubscriptionOptions = {
    enabled: boolean;
    onEvent: (event: RealtimeEvent) => void;
};

const REALTIME_RECONNECT_DELAY_MS = 2000;

export function useRealtimeStreamSubscription({
    enabled,
    onEvent,
}: UseRealtimeStreamSubscriptionOptions): void {
    const { streamRealtimeEvents, normalizeEventsStreamError } = useEventsApi();
    const { isDesktop, status } = useServerConnectivity();
    const streamAbortRef = useRef<AbortController | null>(null);
    const retryTimerRef = useRef<number | null>(null);
    const connectivityEnabled = !isDesktop || status === "online";

    useEffect(() => {
        if (!enabled || !connectivityEnabled) {
            return;
        }
        if (import.meta.env.MODE === "test") {
            return;
        }

        let active = true;

        const cleanup = () => {
            streamAbortRef.current?.abort();
            streamAbortRef.current = null;
            if (retryTimerRef.current !== null) {
                window.clearTimeout(retryTimerRef.current);
                retryTimerRef.current = null;
            }
        };

        const connect = () => {
            if (!active) {
                return;
            }

            cleanup();
            const controller = new AbortController();
            streamAbortRef.current = controller;

            void streamRealtimeEvents({
                signal: controller.signal,
                onEvent,
                onError: (streamError) => {
                    const detail = normalizeEventsStreamError(streamError);
                    if (detail.message) {
                        console.debug("[realtime] stream event parse error:", detail.message);
                    }
                },
            })
                .catch((streamError) => {
                    const detail = normalizeEventsStreamError(streamError);
                    if (detail.message) {
                        console.debug("[realtime] stream connection closed:", detail.message);
                    }
                })
                .finally(() => {
                    if (!active || controller.signal.aborted) {
                        return;
                    }
                    retryTimerRef.current = window.setTimeout(() => {
                        connect();
                    }, REALTIME_RECONNECT_DELAY_MS);
                });
        };

        connect();

        return () => {
            active = false;
            cleanup();
        };
    }, [connectivityEnabled, enabled, normalizeEventsStreamError, onEvent, streamRealtimeEvents]);
}
