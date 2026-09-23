import { useMemo } from "react";

import { normalizeEventsStreamError } from "../../../api/events/eventsError";
import * as eventsApi from "../../../api/events/eventsApi";

export type {
    RealtimeEvent,
    RealtimeEventType,
    APIKeyRealtimeEventType,
} from "../../../api/events/eventsApi";

export function useEventsApi() {
    return useMemo(
        () => ({
            ...eventsApi,
            normalizeEventsStreamError,
        }),
        [],
    );
}
