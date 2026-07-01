export type DesktopPlatform = "linux" | "macos" | "unknown" | "windows";

type TauriWindow = Window & { __TAURI_INTERNALS__?: unknown };

export function isTauriRuntime(runtimeWindow?: Window): boolean {
    return Boolean(runtimeWindow && "__TAURI_INTERNALS__" in (runtimeWindow as TauriWindow));
}

export function detectDesktopPlatform(userAgent: string): DesktopPlatform {
    if (/Macintosh|Mac OS X/i.test(userAgent)) return "macos";
    if (/Windows/i.test(userAgent)) return "windows";
    if (/Linux/i.test(userAgent)) return "linux";
    return "unknown";
}

export function initializeDesktopRuntime(): void {
    if (typeof window === "undefined" || !isTauriRuntime(window)) return;

    document.documentElement.dataset.tauriRuntime = "true";
    document.documentElement.dataset.tauriPlatform = detectDesktopPlatform(
        window.navigator.userAgent,
    );
}
