import { useEffect, useState } from "react";

import { getApiBase } from "../api/http";

type AppConfig = {
  login_enabled?: boolean;
  api_base_path?: string;
  frontend_base_path?: string;
};

export function useAppConfig() {
  const [data, setData] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      try {
        const response = await fetch(`${getApiBase()}/config`, { credentials: "include" });
        if (!response.ok) return;
        const payload = (await response.json()) as AppConfig;
        setData(payload);
      } finally {
        setLoading(false);
      }
    };
    void run();
  }, []);

  return { data, loading };
}
