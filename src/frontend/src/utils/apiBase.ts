function resolveDefaultApiBase(): string {
    if (typeof window !== "undefined" && window.location?.origin) {
        return window.location.origin;
    }
    return "http://localhost:8000";
}

const API_BASE = import.meta.env.VITE_API_BASE_URL?.trim() || resolveDefaultApiBase();

export function getApiBase(): string {
    return API_BASE.replace(/\/+$/, "");
}
