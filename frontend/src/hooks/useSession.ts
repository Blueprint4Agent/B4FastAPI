import { useSyncExternalStore } from "react";

import { getAccessToken, subscribeToken } from "../store/session";

// Agent note: any token storage changes should keep this hook contract stable.
export function useAccessToken() {
    return useSyncExternalStore(subscribeToken, getAccessToken, getAccessToken);
}
