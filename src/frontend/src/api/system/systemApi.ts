import { getApiBase } from "../../utils/apiBase";

export type ServerReadiness = {
    status: "ok" | "degraded";
    checks: Record<string, string>;
};

const SERVER_READINESS_PATH = "/health/ready";

export async function getServerReadiness(signal?: AbortSignal): Promise<ServerReadiness> {
    const response = await fetch(`${getApiBase()}${SERVER_READINESS_PATH}`, {
        method: "GET",
        headers: {
            Accept: "application/json",
            "Cache-Control": "no-cache",
        },
        cache: "no-store",
        credentials: "include",
        signal,
    });

    if (!response.ok) {
        throw new Error(`Server readiness check failed (${response.status}).`);
    }

    const payload = (await response.json()) as Partial<ServerReadiness>;
    if (payload.status !== "ok") {
        throw new Error(`Server is not ready (${payload.status ?? "unknown"}).`);
    }

    return {
        status: payload.status,
        checks: payload.checks ?? {},
    };
}
