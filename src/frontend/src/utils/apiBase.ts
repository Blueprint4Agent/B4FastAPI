function resolveDefaultApiBase(): string {
    if (typeof window !== "undefined" && window.location?.origin) {
        if (window.location.port === "5173") {
            return `${window.location.protocol}//${window.location.hostname}:8000`;
        }
        return window.location.origin;
    }
    return "http://localhost:8000";
}

const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

export function alignLoopbackApiBase(apiBase: string, frontendHostname: string): string {
    try {
        const apiUrl = new URL(apiBase);
        if (LOOPBACK_HOSTS.has(apiUrl.hostname) && LOOPBACK_HOSTS.has(frontendHostname)) {
            apiUrl.hostname = frontendHostname;
            return apiUrl.toString();
        }
    } catch {
        return apiBase;
    }
    return apiBase;
}

function resolveApiBase(): string {
    const configuredBase = import.meta.env.VITE_API_BASE_URL?.trim();
    if (!configuredBase) {
        return resolveDefaultApiBase();
    }
    if (typeof window === "undefined" || !window.location?.hostname) {
        return configuredBase;
    }
    return alignLoopbackApiBase(configuredBase, window.location.hostname);
}

const API_BASE = resolveApiBase();

export function getApiBase(): string {
    return API_BASE.replace(/\/+$/, "");
}
