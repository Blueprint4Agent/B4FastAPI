import { useEffect, useState } from "react";

import { apiClient } from "../api/http";
import type { paths } from "../api/generated/openapi";

type AppConfig = paths["/config"]["get"]["responses"][200]["content"]["application/json"];

export function useAppConfig() {
    const [data, setData] = useState<AppConfig | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const run = async () => {
            try {
                const { data: payload, error } = await apiClient.GET("/config");
                if (!error && payload) {
                    setData(payload);
                }
            } finally {
                setLoading(false);
            }
        };
        void run();
    }, []);

    return { data, loading };
}
