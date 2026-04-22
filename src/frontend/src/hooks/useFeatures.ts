import { useEffect, useState } from "react";

import type { AppConfig } from "../api/config/configApi";
import { useConfigApi } from "./api/config/useConfigApi";

export function useAppConfig() {
    const { getConfig } = useConfigApi();
    const [data, setData] = useState<AppConfig | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const run = async () => {
            try {
                const payload = await getConfig();
                setData(payload);
            } finally {
                setLoading(false);
            }
        };
        void run();
    }, [getConfig]);

    return { data, loading };
}
