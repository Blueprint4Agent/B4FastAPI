const ACCESS_TOKEN_KEY = "template_access_token";

type Listener = () => void;
const listeners = new Set<Listener>();

let accessTokenCache: string | null = null;

function notify() {
    listeners.forEach((listener) => listener());
}

function readTokenFromStorage() {
    try {
        return sessionStorage.getItem(ACCESS_TOKEN_KEY);
    } catch {
        return null;
    }
}

export function getAccessToken(): string | null {
    if (accessTokenCache !== null) {
        return accessTokenCache;
    }
    accessTokenCache = readTokenFromStorage();
    return accessTokenCache;
}

export function setAccessToken(token: string) {
    accessTokenCache = token;
    try {
        sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
    } catch {
        // ignore storage errors in restricted browser contexts
    }
    notify();
}

export function clearAccessToken() {
    accessTokenCache = null;
    try {
        sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    } catch {
        // ignore storage errors in restricted browser contexts
    }
    notify();
}

export function subscribeToken(listener: Listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
}
