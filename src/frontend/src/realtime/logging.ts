import type { RealtimeEvent } from "../hooks/api/events/useEventsApi";

const REALTIME_SYSTEM_EVENT_TYPES = new Set<string>(["connected", "ping"]);

export function isSystemRealtimeEvent(eventType: string): boolean {
    return REALTIME_SYSTEM_EVENT_TYPES.has(eventType);
}

export function logRealtimeServiceEvent(
    event: RealtimeEvent,
    metadata: Record<string, unknown> = {},
): void {
    if (isSystemRealtimeEvent(event.type)) {
        return;
    }
    console.debug("[realtime] service event received:", event.type, {
        eventId: event.id,
        ...metadata,
    });
}
