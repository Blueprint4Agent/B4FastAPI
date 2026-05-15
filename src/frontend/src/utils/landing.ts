const LANDING_STARTED_STORAGE_KEY = "b4fastapi:landing:v1:started";

export function hasStartedFromLanding(): boolean {
    if (typeof window === "undefined") {
        return false;
    }
    return window.localStorage.getItem(LANDING_STARTED_STORAGE_KEY) === "true";
}

export function markLandingStarted(): void {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.setItem(LANDING_STARTED_STORAGE_KEY, "true");
}
