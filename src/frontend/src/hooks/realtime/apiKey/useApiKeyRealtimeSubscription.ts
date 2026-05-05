import { useCallback } from "react";

import type { APIKeyRecord } from "../../api/apiKey/useApiKeyApi";
import type { RealtimeEvent } from "../../api/events/useEventsApi";
import { logRealtimeServiceEvent } from "../../../realtime/logging";
import { useRealtimeStreamSubscription } from "../core/useRealtimeStreamSubscription";

type UseAPIKeyRealtimeSubscriptionOptions = {
    enabled: boolean;
    onCreated: (apiKey: APIKeyRecord) => void;
    onStatusUpdated: (apiKey: APIKeyRecord) => void;
    onDeleted: (apiKey: APIKeyRecord) => void;
};

type APIKeyRealtimeEventType = "api_key.created" | "api_key.status_updated" | "api_key.deleted";

function isAPIKeyRealtimeEventType(type: string): type is APIKeyRealtimeEventType {
    return (
        type === "api_key.created" ||
        type === "api_key.status_updated" ||
        type === "api_key.deleted"
    );
}

function extractAPIKeyRecord(event: RealtimeEvent): APIKeyRecord | null {
    const rawAPIKey = event.payload?.api_key;
    if (!rawAPIKey || typeof rawAPIKey !== "object") {
        return null;
    }
    if (typeof (rawAPIKey as { id?: unknown }).id !== "number") {
        return null;
    }
    return rawAPIKey as APIKeyRecord;
}

export function useApiKeyRealtimeSubscription({
    enabled,
    onCreated,
    onStatusUpdated,
    onDeleted,
}: UseAPIKeyRealtimeSubscriptionOptions): void {
    const handleEvent = useCallback(
        (event: RealtimeEvent) => {
            if (!isAPIKeyRealtimeEventType(event.type)) {
                return;
            }

            const apiKey = extractAPIKeyRecord(event);
            if (!apiKey) {
                return;
            }

            logRealtimeServiceEvent(event, { apiKeyId: apiKey.id });
            if (event.type === "api_key.created") {
                onCreated(apiKey);
                return;
            }
            if (event.type === "api_key.status_updated") {
                onStatusUpdated(apiKey);
                return;
            }
            onDeleted(apiKey);
        },
        [onCreated, onDeleted, onStatusUpdated],
    );

    useRealtimeStreamSubscription({
        enabled,
        onEvent: handleEvent,
    });
}
