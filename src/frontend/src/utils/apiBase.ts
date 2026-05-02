function resolveDefaultApiBase(): string {
    if (typeof window !== "undefined" && window.location?.origin) {
        if (window.location.port === "5173") {
            return `${window.location.protocol}//${window.location.hostname}:8000`;
        }
        return window.location.origin;
    }
    return "http://localhost:8000";
}

const API_BASE = import.meta.env.VITE_API_BASE_URL?.trim() || resolveDefaultApiBase();

export function getApiBase(): string {
    return API_BASE.replace(/\/+$/, "");
}
