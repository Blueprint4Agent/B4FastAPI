import { useCallback, useEffect, useRef, useState } from "react";

import type { AppConfig } from "../api/config/configApi";
import { useConfigApi } from "./api/config/useConfigApi";
import { useServerConnectivity } from "./connectivity/useServerConnectivity";

export function useAppConfig() {
    const { getConfig } = useConfigApi();
    const { isDesktop, status } = useServerConnectivity();
    const [data, setData] = useState<AppConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const disconnectedRef = useRef(false);

    const loadConfig = useCallback(async () => {
        try {
            const payload = await getConfig();
            setData(payload);
        } finally {
            setLoading(false);
        }
    }, [getConfig]);

    useEffect(() => {
        void loadConfig().catch(() => undefined);
    }, [loadConfig]);

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
            void loadConfig().catch(() => undefined);
        }
    }, [isDesktop, loadConfig, status]);

    return { data, loading };
}
