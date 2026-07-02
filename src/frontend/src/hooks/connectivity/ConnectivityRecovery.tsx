import { useEffect, useRef } from "react";

import { useAuthContext } from "../useAuth";
import { useServerConnectivity } from "./useServerConnectivity";

export function ConnectivityRecovery() {
    const { revalidateSession } = useAuthContext();
    const { isDesktop, status } = useServerConnectivity();
    const disconnectedRef = useRef(false);

    useEffect(() => {
        if (!isDesktop) {
            return;
        }
        if (status === "offline" || status === "reconnecting") {
            disconnectedRef.current = true;
            return;
        }
        if (status === "online" && disconnectedRef.current) {
            disconnectedRef.current = false;
            void revalidateSession();
        }
    }, [isDesktop, revalidateSession, status]);

    return null;
}
