import { getAccessToken } from "../store/session";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = RequestInit & {
  auth?: boolean;
};

export type APIError = {
  detail?: {
    error?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

export function getApiBase(): string {
  return API_BASE.replace(/\/+$/, "");
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers ?? {});
  headers.set("Content-Type", "application/json");

  if (options.auth) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${getApiBase()}${path}`, {
    ...options,
    headers,
    credentials: "include"
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw payload;
  }
  return payload as T;
}
